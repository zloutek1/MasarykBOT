from discord import HTTPException, NotFound
from discord.ext import commands

import os
import re
import asyncio
import aiohttp
import textwrap
import logging
import contextlib
from signal import Signals
from functools import partial
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

log = logging.getLogger(__name__)

ESCAPE_REGEX = re.compile("[`\u202E\u200B]{3,}")
FORMATTED_CODE_REGEX = re.compile(
    r"^\s*"                                 # any leading whitespace from the beginning of the string
    r"(?P<delim>(?P<block>```)|``?)"        # code delimiter: 1-3 backticks; (?P=block) only matches if it's a block
    r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"    # if we're in a block, match optional language (only letters plus newline)
    r"(?:[ \t]*\n)*"                        # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"                        # extract all code inside the markup
    r"\s*"                                  # any more whitespace before the end of the code markup
    r"(?P=delim)"                           # match the exact same delimiter from the start again
    r"\s*$",                                # any trailing whitespace until the end of the string
    re.DOTALL | re.IGNORECASE               # "." also matches newlines, case insensitive
)
RAW_CODE_REGEX = re.compile(
    r"^(?:[ \t]*\n)*"                       # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"                        # extract all the rest as code
    r"\s*$",                                # any trailing whitespace until the end of the string
    re.DOTALL                               # "." also matches newlines
)

SIGKILL = 9
REEVAL_EMOJI = '\U0001f501'  # :repeat:


class Snekbox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jobs = {}

    async def post_eval(self, code: str) -> dict:
        """Send a POST request to the Snekbox API to evaluate code and return the results."""
        url = os.getenv("SNEKBOX") % os.getenv("PORT", 8060)
        data = {"input": code}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, raise_for_status=True) as resp:
                return await resp.json()

    @staticmethod
    def prepare_input(code: str) -> str:
        """Extract code from the Markdown, format it, and insert it into the code template."""
        match = FORMATTED_CODE_REGEX.fullmatch(code)
        if match:
            code, block, lang, delim = match.group("code", "block", "lang", "delim")
            code = textwrap.dedent(code)
            if block:
                info = (f"'{lang}' highlighted" if lang else "plain") + " code block"
            else:
                info = f"{delim}-enclosed inline code"
            log.info(f"Extracted {info} for evaluation:\n{code}")
        else:
            code = textwrap.dedent(RAW_CODE_REGEX.fullmatch(code).group("code"))
            log.info(
                f"Eval message contains unformatted or badly formatted code, "
                f"stripping whitespace only:\n{code}"
            )

        return code

    @staticmethod
    def get_results_message(results):
        """Return a user-friendly message and error corresponding to the process's return code."""
        stdout, returncode = results["stdout"], results["returncode"]
        msg = f"Your eval job has completed with return code {returncode}"
        error = ""

        if returncode is None:
            msg = "Your eval job has failed"
            error = stdout.strip()
        elif returncode == 128 + SIGKILL:
            msg = "Your eval job timed out or ran out of memory"
        elif returncode == 255:
            msg = "Your eval job has failed"
            error = "A fatal NsJail error occurred"
        else:
            # Try to append signal's name if one exists
            try:
                name = Signals(returncode - 128).name
                msg = f"{msg} ({name})"
            except ValueError:
                pass

        return msg, error

    async def format_output(self, output):
        """
        Format the output and return a tuple of the formatted output and a URL to the full output.
        Prepend each line with a line number. Truncate if there are over 10 lines or 1000 characters
        and upload the full output to a paste service.
        """
        log.info("Formatting output...")

        output = output.rstrip("\n")

        if "<@" in output:
            output = output.replace("<@", "<@\u200B")  # Zero-width space

        if "<!@" in output:
            output = output.replace("<!@", "<!@\u200B")  # Zero-width space

        if ESCAPE_REGEX.findall(output):
            return "Code block escape attempt detected; will not output result"

        lines = output.count("\n")

        if lines > 0:
            output = [f"{i:03d} | {line}" for i, line in enumerate(output.split('\n'), 1)]
            output = output[:11]  # Limiting to only 11 lines
            output = "\n".join(output)

        if lines > 10:
            if len(output) >= 1000:
                output = f"{output[:1000]}\n... (truncated - too long, too many lines)"
            else:
                output = f"{output}\n... (truncated - too many lines)"
        elif len(output) >= 1000:
            output = f"{output[:1000]}\n... (truncated - too long)"

        output = output or "[No output]"

        return output

    @staticmethod
    def get_status_emoji(results):
        """Return an emoji corresponding to the status code or lack of output in result."""
        if not results["stdout"].strip():  # No output
            return ":warning:"
        elif results["returncode"] == 0:  # No error
            return ":white_check_mark:"
        else:  # Exception
            return ":x:"

    async def send_eval(self, ctx, code):
        """
        Evaluate code, format it, and send the output to the corresponding channel.
        Return the bot response.
        """
        async with ctx.typing():
            results = await self.post_eval(code)
            msg, error = self.get_results_message(results)

            if error:
                output = error
            else:
                output = await self.format_output(results["stdout"])

            icon = self.get_status_emoji(results)
            msg = f"{ctx.author.mention} {icon} {msg}.\n\n```\n{output}\n```"

            log.info(f"{ctx.author}'s job had a return code of {results['returncode']}")
            return await ctx.send(msg)

    async def get_code(self, message):
        """
        Return the code from `message` to be evaluated.
        If the message is an invocation of the eval command, return the first argument or None if it
        doesn't exist. Otherwise, return the full content of the message.
        """
        log.info(f"Getting context for message {message.id}.")
        new_ctx = await self.bot.get_context(message)

        if new_ctx.command is self.eval_command:
            log.info(f"Message {message.id} invokes eval command.")
            split = message.content.split(maxsplit=1)
            code = split[1] if len(split) > 1 else None
        else:
            log.info(f"Message {message.id} does not invoke eval command.")
            code = message.content

        return code

    @commands.command(name="eval", aliases=("e",))
    async def eval_command(self, ctx, *, code) -> None:
        if ctx.author.id in self.jobs:
            await ctx.send(
                f"{ctx.author.mention} You've already got a job running - "
                "please wait for it to finish!"
            )
            return

        while True:
            self.jobs[ctx.author.id] = datetime.now()
            code = self.prepare_input(code)
            try:
                response = await self.send_eval(ctx, code)
            finally:
                del self.jobs[ctx.author.id]

            code = await self.continue_eval(ctx, response)
            if not code:
                break
            log.info(f"Re-evaluating code from message {ctx.message.id}:\n{code}")

    async def continue_eval(self, ctx, response):
        """
        Check if the eval session should continue.
        Return the new code to evaluate or None if the eval session should be terminated.
        """
        _predicate_eval_message_edit = partial(predicate_eval_message_edit, ctx)
        _predicate_emoji_reaction = partial(predicate_eval_emoji_reaction, ctx)

        with contextlib.suppress(NotFound):
            try:
                _, new_message = await self.bot.wait_for(
                    'message_edit',
                    check=_predicate_eval_message_edit,
                    timeout=30
                )
                await ctx.message.add_reaction(REEVAL_EMOJI)
                await self.bot.wait_for(
                    'reaction_add',
                    check=_predicate_emoji_reaction,
                    timeout=10
                )

                code = await self.get_code(new_message)
                await ctx.message.clear_reactions()
                with contextlib.suppress(HTTPException):
                    await response.delete()

            except asyncio.TimeoutError:
                await ctx.message.clear_reactions()
                return None

            return code


def predicate_eval_message_edit(ctx, old_msg, new_msg):
    """Return True if the edited message is the context message and the content was indeed modified."""
    return new_msg.id == ctx.message.id and old_msg.content != new_msg.content


def predicate_eval_emoji_reaction(ctx, reaction, user) -> bool:
    """Return True if the reaction REEVAL_EMOJI was added by the context message author on this message."""
    return reaction.message.id == ctx.message.id and user.id == ctx.author.id and str(reaction) == REEVAL_EMOJI


def setup(bot):
    bot.add_cog(Snekbox(bot))
