from discord import Color, Embed, File
from discord.ext import commands
import time
import os

"""
All Process classes where taken from
https://github.com/SFTtech/kevin/blob/master/kevin/process.py
with slight modification
"""

import asyncio
import asyncio.streams
import signal
import subprocess
import sys


INF = float("inf")


class AsyncWith:
    """
    Base class for objects that are usable with `async with` only.
    """

    def __enter__(self):
        raise Exception("use async with!")

    def __exit__(self, exc, value, traceback):
        raise Exception("use async with!")


class ProcessError(subprocess.SubprocessError):
    """
    Generic process error.
    """

    def __init__(self, msg):
        super().__init__(msg)

    def __str__(self):
        return f"Process failed: {self}"


class LineReadError(ProcessError):
    """
    We could not read the requested amount of lines!
    """

    def __init__(self, msg, cmd):
        super().__init__(msg)
        self.cmd = cmd


class ProcTimeoutError(ProcessError):
    """
    A subprocess can timeout because it took to long to finish or
    no output was received for a given time period.
    This exception is raised and stores whether it just took too long,
    or did not respond in time to provide any new output.
    """

    def __init__(self, cmd, timeout, was_global=False):
        super().__init__("Process timeout")
        self.cmd = cmd
        self.timeout = timeout
        self.was_global = was_global

    def __str__(self):
        return ("Command timed out after %s seconds" % self.timeout)


class ProcessFailed(ProcessError):
    """
    The executed process returned with a non-0 exit code
    """

    def __init__(self, returncode, cmd):
        super().__init__("Process failed")
        self.returncode = returncode
        self.cmd = cmd

    def __str__(self):
        if self.returncode and self.returncode < 0:
            try:
                return "Process '%s' died with %r." % (
                    self.cmd, signal.Signals(-self.returncode))
            except ValueError:
                return "Process '%s' died with unknown signal %d." % (
                    self.cmd, -self.returncode)
        else:
            return "Process '%s' returned non-zero exit status %d." % (
                self.cmd, self.returncode)


class Process(AsyncWith):
    """
    Contains a running process specified by command.

    You really should use this in `async with Process(...) as proc:`.

    Main feature: interact/communicate with the process multiple times.
    You can repeatedly send data to stdin and fetch the replies.

    chop_lines: buffer for lines
    must_succeed: throw ProcessFailed on non-0 exit
    pipes: True=create pipes to the process, False=reuse your terminal
    loop: the event loop to run this process in
    linebuf_max: maximum size of the buffer for line chopping
    queue_size: maximum number of entries in the output queue
    """

    def __init__(self, command, chop_lines=False, must_succeed=False,
                 pipes=True, loop=None,
                 linebuf_max=(8 * 1024 ** 2), queue_size=1024):

        self.loop = loop or asyncio.get_event_loop()

        self.created = False

        # future to track force-exit exceptions.
        # this contains the exception if the program
        # was killed e.g. because of a timeout.
        self.killed = self.loop.create_future()

        pipe = subprocess.PIPE if pipes else None
        self.capture_data = pipes

        self.proc = self.loop.subprocess_exec(
            lambda: WorkerInteraction(self, chop_lines,
                                      linebuf_max, queue_size),
            *command,
            stdin=pipe, stdout=pipe, stderr=pipe)

        self.args = command
        self.chop_lines = chop_lines
        self.must_succeed = must_succeed

        self.transport = None
        self.protocol = None

        self.exit_callbacks = list()

    async def create(self):
        """ Launch the process """
        if self.created:
            raise Exception("process already created")

        # print("creating process '%s'..." % self.args)

        self.transport, self.protocol = await self.proc
        self.created = True

    def communicate(self, data=None, timeout=INF,
                    output_timeout=INF, linecount=INF):
        """
        Interacts with the process io streams.

        You get an asynchronous iterator for `async for`:
        Use it as `async for (fd, data) in proc.communicate(...):`.

        Can feed data to stdin.

        if linecount is finite:
            The iterator will return the number of requested lines.
            Output from stderr is returned as well, but not counted.

        else:
            Runs until the process terminates or times out.
            returns chunks as they come from the process.
        """

        if not self.created:
            raise Exception("can't communicate as process was not yet created")

        if not self.capture_data:
            raise Exception("pipes=False, but you wanted to communicate()")

        if linecount < INF and not self.chop_lines:
            raise Exception("can't do line counting when it's disabled "
                            "upon process creation (chop_lines)")

        return ProcessIterator(self, self.loop, data, timeout,
                               output_timeout, linecount)

    def readline(self, data=None, timeout=INF):
        """ send data to stdin and read one line of response data """
        return self.communicate(data, output_timeout=timeout, linecount=1)

    def returncode(self):
        """ get the exit code, or None if still running """
        if not self.transport:
            raise Exception("Process has never run!")

        return self.transport.get_returncode()

    async def wait(self):
        """ wait for exit and return the exit code. """
        return await self.transport._wait()

    async def wait_for(self, timeout=None):
        """
        Wait a limited time for exit and return the exit code.
        raise ProcTimeoutError if it took too long.
        """
        try:
            return await asyncio.wait_for(self.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise ProcTimeoutError(self.args, timeout)

    async def pwn(self, term_timeout=5):
        """
        make sure the process is dead (terminate, kill, wait)
        return the exit code.
        """

        # TODO: if this poll is removed,
        #       the process may be terminated
        #       but the pid is no longer running!??
        if self.transport and self.transport._proc:
            self.transport._proc.poll()

        # check if the process already exited
        ret = self.returncode()

        if ret is not None:
            return ret

        try:
            self.terminate()
            return await asyncio.wait_for(self.wait(), timeout=term_timeout)

        except asyncio.TimeoutError:
            self.kill()
            return await self.wait()

    def send_signal(self, sig):
        """ send a signal to the process """
        self.transport.send_signal(sig)

    def terminate(self):
        """ send sigterm to the process """
        self.transport.terminate()

    def kill(self):
        """ send sigkill to the process """
        self.transport.kill()

    def on_exit(self, callback):
        """
        call the callback when the process exited
        callback() is called.
        """
        if not callable(callback):
            raise ValueError(f"invalid callback: {callback}")

        self.exit_callbacks.append(callback)

    def fire_exit_callbacks(self):
        """
        Called from the protocol when the process exited.
        """
        for callback in self.exit_callbacks:
            callback()

    async def __aenter__(self):
        await self.create()
        return self

    async def __aexit__(self, exc, value, traceback):
        await self.pwn()


class WorkerInteraction(asyncio.streams.FlowControlMixin,
                        asyncio.SubprocessProtocol):
    """
    Subprocess protocol specialization to allow output line buffering.
    """

    def __init__(self, process, chop_lines, linebuf_max, queue_size=INF):
        super().__init__()
        self.process = process
        self.buf = bytearray()
        self.transport = None
        self.stdin = None
        self.linebuf_max = linebuf_max
        self.queue = asyncio.Queue(maxsize=(
            queue_size if queue_size < INF else 0))
        self.chop_lines = chop_lines

    def connection_made(self, transport):
        self.transport = transport

        stdin_transport = self.transport.get_pipe_transport(0)
        self.stdin = asyncio.StreamWriter(stdin_transport,
                                          protocol=self,
                                          reader=None,
                                          loop=asyncio.get_event_loop())

    def pipe_connection_lost(self, fdnr, exc):
        """
        the given fd is no longer connected.
        """
        del exc
        self.transport.get_pipe_transport(fdnr).close()

    def process_exited(self):
        # process exit happens after all the pipes were lost.

        # print("Process %s exited" % self.process)

        # send out remaining data to queue
        if self.buf:
            self.enqueue_data((1, bytes(self.buf)))
            del self.buf[:]

        # mark the end-of-stream
        self.enqueue_data(StopIteration)
        self.transport.close()
        self.process.fire_exit_callbacks()

    async def write(self, data):
        """
        Wait until data was written to the process stdin.
        """
        self.stdin.write(data)
        # TODO: really drain?
        await self.stdin.drain()

    def pipe_data_received(self, fdnr, data):
        if len(self.buf) + len(data) > self.linebuf_max:
            raise ProcessError("too much data")

        if fdnr == 1:
            # add data to buffer
            self.buf.extend(data)

            if self.chop_lines:
                npos = self.buf.rfind(b"\n")

                if npos < 0:
                    return

                lines = self.buf[:npos].split(b"\n")

                for line in lines:
                    self.enqueue_data((fdnr, bytes(line)))

                del self.buf[:(npos + 1)]

            # no line chopping
            else:
                self.enqueue_data((fdnr, bytes(self.buf)))
                del self.buf[:]
        else:
            # non-stdout data:
            self.enqueue_data((fdnr, data))

    def enqueue_data(self, data):
        """
        Add data so it can be sent to the process.
        """
        try:
            self.queue.put_nowait(data)
        except asyncio.QueueFull as exc:
            if not self.process.killed.done():
                self.process.killed.set_exception(exc)


class ProcessIterator:
    """
    Aasynchronous iterator for the process output.
    Interacts with its process and provides output.

    use like `async for (fd, data) in ProcessIterator(...):`
    """

    def __init__(self, process, loop, data=None, run_timeout=INF,
                 output_timeout=INF, linecount=INF):
        """
        data: will be fed to stdin of process.
        timeout: the iteration will only take this amount of time.
        output_timeout: one iteration stel may only take this long.
        linecount: the number of lines we want to receive.
        """
        self.process = process
        self.loop = loop

        self.data = data
        self.run_timeout = run_timeout
        self.output_timeout = output_timeout
        self.linecount = linecount

        self.lines_emitted = 0
        self.line_timer = None
        self.overall_timer = None

        if self.run_timeout < INF:
            # set the global timer
            self.overall_timer = self.loop.call_later(
                self.run_timeout,
                lambda: self.timeout(was_global=True))

    def timeout(self, was_global=False):
        """
        Called when the process times out.
        line_output: it was the line-timeout that triggered.
        """

        if not self.process.killed.done():
            self.process.killed.set_exception(ProcTimeoutError(
                self.process.args,
                self.run_timeout if was_global else self.output_timeout,
                was_global,
            ))

    async def __aiter__(self):
        """
        Yields tuples of (fd, data) where fd is one of
        {stdout_fileno, stderr_fileno}, and data is the bytes object
        that was written to that stream (may be a line if requested).

        If the process times out or some error occurs,
        this function will raise the appropriate exception.
        """

        while True:
            # cancel the previous line timeout
            if self.output_timeout < INF:
                if self.line_timer:
                    self.line_timer.cancel()

                # and set the new one
                self.line_timer = self.loop.call_later(
                    self.output_timeout,
                    lambda: self.timeout(was_global=False))

            # send data to stdin
            if self.data:
                await self.process.protocol.write(self.data)
                self.data = None

            # we emitted enough lines
            if self.lines_emitted >= self.linecount:
                # stop the iteration as there were enough lines
                self.error_check()
                return

            # now, either the process exits,
            # there's an exception (process will be killed)
            # or the queue gives us the next data item.
            # wait for the first of those events.
            done, pending = await asyncio.wait(
                [self.process.protocol.queue.get(), self.process.killed],
                return_when=asyncio.FIRST_COMPLETED)

            # at least one of them is done now:
            for future in done:
                # if something failed, cancel the pending futures
                # and raise the exception
                # this happens e.g. for a timeout.
                if future.exception():
                    for future_pending in pending:
                        future_pending.cancel()

                    for future_pending in pending:
                        try:
                            await future_pending
                        except asyncio.CancelledError:
                            pass

                    # kill the process before throwing the error!
                    await self.process.pwn()
                    raise future.exception()

                # fetch output from the process
                entry = future.result()

                # The result is StopIteration to indicate that the process
                # output stream ended.
                if entry is StopIteration:
                    # no more data, so stop iterating
                    self.error_check()
                    return

                fdnr, data = entry

                # only count stdout lines
                if fdnr == 1:
                    self.lines_emitted += 1

                yield fdnr, data

    def error_check(self):
        """
        Check if the number of read lines is expected.

        This is called either when the process exited,
        or when enough lines were read.
        """

        # cancel running timers as we're terminating anyway
        if self.line_timer:
            self.line_timer.cancel()

        if self.overall_timer:
            self.overall_timer.cancel()

        retcode = self.process.returncode()

        if self.process.must_succeed:
            if retcode is not None and retcode != 0:
                raise ProcessFailed(retcode, self.process.args)

        # check if we received enough lines
        if self.linecount < INF and self.lines_emitted < self.linecount:
            # received 0 lines:
            if self.lines_emitted == 0:
                raise ProcessError("process did not provide any stdout lines")
            else:
                raise LineReadError("could only read %d of %d line%s" % (
                    self.lines_emitted, self.linecount,
                    "s" if self.linecount > 1 else ""), self.process.args)


async def eval_coro(body):
    """
    place the body into eval_template.py file
    save the file into a TemporaryFile
    execute the file in Process() class
        quit the file execution after 5 seconds
        if the QueueFull error occures, there probably was an infinite loop
        return the output lines if everything went smoothly
    """
    with open("assets/eval_template.py", "r") as file:
        to_compile = file.read().replace("{{{body}}}", body.strip())

    tempimage = None
    import tempfile
    prog = tempfile.NamedTemporaryFile()
    prog.write(bytes(to_compile, "utf-8"))
    prog.flush()

    async with Process([sys.executable, '-u', prog.name],
                       chop_lines=True) as proc:
        lines = []
        try:
            async for fdn, line in proc.communicate(output_timeout=5, timeout=5):
                lines.append(line.decode("utf-8"))

            if os.path.isfile(f"{prog.name}.jpg"):
                tempimage = f"{prog.name}.jpg"

        except asyncio.queues.QueueFull:
            return 2, "Infinite loop, code terminated", tempimage

        except ProcTimeoutError as exc:
            return 1, exc, tempimage

        else:
            return 0, "\n".join(lines), tempimage


class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body):
        """
        check if the body is executable
        check for blocked_words which could be potentionally harmful

        call eval_coro method

        format embed in format
            ``` code ```
            Finished in: 00:00:00

        set color and reaction depending on success / error

        remove play reaction so the code can't be executed
        again
        """
        if not self.is_evaluatable_message(body):
            return

        blocked_words = ['delete', 'os', 'subprocess', 'open',
                         'history()', '("token")', "('token')"]

        if ctx.author.id != self.bot.owner_id:
            for x in blocked_words:
                if x in body.lower():
                    embed = Embed(color=Color.red())
                    embed.add_field(
                        name="Error", value=f'```\nYour code contains certain blocked words.\n```')
                    embed.set_footer(icon_url=ctx.author.avatar_url)
                    return await ctx.send(embed=embed)

        body = self.cleanup_code(body)
        err = out = None
        time_start = time.time()

        embed = Embed(color=Color(0xffffcc))

        def paginate(text: str):
            '''Simple generator that paginates text.'''
            last = 0
            pages = []
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != '', pages))

        # eval body
        ret_code, value, image = await eval_coro(body)

        time_end = time.time()
        elapsed_time = time.strftime(
            "%H:%M:%S", time.gmtime(time_end - time_start))

        if ret_code == 0:
            dots = "..." if len(value) > 1000 else ""
            embed.add_field(
                name="Output", value=f'```py\n{value[:1000]}{dots}\n```')
            embed.set_footer(
                text=f"Finished in: {elapsed_time}", icon_url=ctx.author.avatar_url)

            if image:
                out = await ctx.send(embed=embed, file=File(image))
            else:
                out = await ctx.send(embed=embed)

        else:
            embed.color = Color.red()
            embed.add_field(
                name="Error", value=f'```\n{value}\n```')
            embed.set_footer(
                text=f"Finished in: {elapsed_time}", icon_url=ctx.author.avatar_url)

            if image:
                err = await ctx.send(embed=embed, file=File(image))
            else:
                err = await ctx.send(embed=embed)

        if out:
            await ctx.message.add_reaction('\u2705')  # tick
        elif err:
            await ctx.message.add_reaction('\u2049')  # x
        else:
            await ctx.message.add_reaction('\u2705')

        await ctx.message.remove_reaction("▶", ctx.author)
        await ctx.message.remove_reaction("▶", self.bot.user)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    def is_evaluatable_message(self, body):
        return (body.startswith("```py") and
                body.endswith("```") and
                body.count("\n") >= 2 and
                len(self.cleanup_code(body)) > 0)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.is_evaluatable_message(message.content):
            return

        if message.author.bot:
            return

        await message.add_reaction("▶")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        check if users clicked the play button on executable code
        the bot has to be a reactor on the executable message
        """
        message = reaction.message
        if not self.is_evaluatable_message(message.content):
            return

        if message.author.bot or user.bot or message.author != user:
            return

        if str(reaction.emoji) != "▶":
            return

        if self.bot.user not in await reaction.users().flatten():
            return

        ctx = commands.Context(prefix=self.bot.command_prefix, guild=message.guild,
                               channel=message.channel, message=message, author=user)
        await self._eval.callback(self, ctx, body=message.content)


def setup(bot):
    bot.add_cog(Eval(bot))
