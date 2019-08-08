-- phpMyAdmin SQL Dump
-- version 4.9.0.1
-- https://www.phpmyadmin.net/
--
-- Hostiteľ: localhost
-- Čas generovania: Št 08.Aug 2019, 17:05
-- Verzia serveru: 8.0.17
-- Verzia PHP: 7.2.18

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Databáza: `discordv1.1`
--

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `attachment`
--

CREATE TABLE `attachment` (
  `message_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `filename` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `url` text COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `category`
--

CREATE TABLE `category` (
  `guild_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `position` int(11) NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `channel`
--

CREATE TABLE `channel` (
  `guild_id` bigint(22) NOT NULL,
  `category_id` bigint(22) DEFAULT '0',
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `position` int(11) NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `guild`
--

CREATE TABLE `guild` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `icon_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `leaderboard`
--

CREATE TABLE `leaderboard` (
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `author_id` bigint(22) NOT NULL,
  `messages_sent` int(11) NOT NULL,
  `timestamp` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `member`
--

CREATE TABLE `member` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `avatar_url` text COLLATE utf8mb4_general_ci NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `message`
--

CREATE TABLE `message` (
  `channel_id` bigint(22) NOT NULL,
  `author_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `content` text COLLATE utf8mb4_general_ci NOT NULL,
  `created_at` timestamp NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu`
--

CREATE TABLE `reactionmenu` (
  `id` int(11) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `name` varchar(127) CHARACTER SET utf8 COLLATE utf8_czech_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_option`
--

CREATE TABLE `reactionmenu_option` (
  `id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `emoji` text CHARACTER SET utf8 COLLATE utf8_czech_ci NOT NULL,
  `text` text CHARACTER SET utf8 COLLATE utf8_czech_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

--
-- Spúšťače `reactionmenu_option`
--
DELIMITER $$
CREATE TRIGGER `update_options_count` AFTER INSERT ON `reactionmenu_option` FOR EACH ROW UPDATE `reactionmenu_section` AS sec SET `options`=(SELECT COUNT(*) FROM `reactionmenu_section_option` AS rel INNER JOIN reactionmenu_option AS opt ON rel.message_id = opt.message_id WHERE rel.section_id = sec.id) WHERE 1
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_section`
--

CREATE TABLE `reactionmenu_section` (
  `id` int(11) NOT NULL,
  `reactionmenu_id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `options` int(11) NOT NULL DEFAULT '0',
  `text` varchar(12) CHARACTER SET utf8 COLLATE utf8_czech_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_section_option`
--

CREATE TABLE `reactionmenu_section_option` (
  `section_id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `order_id` int(11) NOT NULL,
  `is_full` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

--
-- Kľúče pre exportované tabuľky
--

--
-- Indexy pre tabuľku `attachment`
--
ALTER TABLE `attachment`
  ADD PRIMARY KEY (`id`),
  ADD KEY `message_id` (`message_id`);

--
-- Indexy pre tabuľku `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `guild` (`guild_id`,`id`) USING BTREE;

--
-- Indexy pre tabuľku `channel`
--
ALTER TABLE `channel`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `guild` (`guild_id`,`category_id`,`id`) USING BTREE,
  ADD KEY `category_id` (`category_id`);

--
-- Indexy pre tabuľku `guild`
--
ALTER TABLE `guild`
  ADD PRIMARY KEY (`id`);

--
-- Indexy pre tabuľku `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD PRIMARY KEY (`guild_id`,`channel_id`,`author_id`) USING BTREE,
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `author_id` (`author_id`);

--
-- Indexy pre tabuľku `member`
--
ALTER TABLE `member`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`id`,`name`) USING BTREE;

--
-- Indexy pre tabuľku `message`
--
ALTER TABLE `message`
  ADD PRIMARY KEY (`id`) USING BTREE,
  ADD KEY `author_id` (`author_id`),
  ADD KEY `channel_id` (`channel_id`);

--
-- Indexy pre tabuľku `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD PRIMARY KEY (`id`,`channel_id`,`name`) USING BTREE,
  ADD KEY `reactionmenu_ibfk_2` (`channel_id`),
  ADD KEY `message_id` (`message_id`);

--
-- Indexy pre tabuľku `reactionmenu_option`
--
ALTER TABLE `reactionmenu_option`
  ADD PRIMARY KEY (`id`),
  ADD KEY `message_id` (`message_id`);

--
-- Indexy pre tabuľku `reactionmenu_section`
--
ALTER TABLE `reactionmenu_section`
  ADD PRIMARY KEY (`id`,`reactionmenu_id`,`text`) USING BTREE,
  ADD KEY `reactionmenu_section_ibfk_1` (`reactionmenu_id`),
  ADD KEY `message_id` (`message_id`);

--
-- Indexy pre tabuľku `reactionmenu_section_option`
--
ALTER TABLE `reactionmenu_section_option`
  ADD PRIMARY KEY (`section_id`,`order_id`) USING BTREE,
  ADD KEY `order_id` (`order_id`),
  ADD KEY `is_full` (`is_full`),
  ADD KEY `message_id` (`message_id`);

--
-- AUTO_INCREMENT pre exportované tabuľky
--

--
-- AUTO_INCREMENT pre tabuľku `reactionmenu`
--
ALTER TABLE `reactionmenu`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pre tabuľku `reactionmenu_option`
--
ALTER TABLE `reactionmenu_option`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pre tabuľku `reactionmenu_section`
--
ALTER TABLE `reactionmenu_section`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pre tabuľku `reactionmenu_section_option`
--
ALTER TABLE `reactionmenu_section_option`
  MODIFY `order_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Obmedzenie pre exportované tabuľky
--

--
-- Obmedzenie pre tabuľku `attachment`
--
ALTER TABLE `attachment`
  ADD CONSTRAINT `attachment_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `category`
--
ALTER TABLE `category`
  ADD CONSTRAINT `category_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `channel`
--
ALTER TABLE `channel`
  ADD CONSTRAINT `channel_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `channel_ibfk_2` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD CONSTRAINT `leaderboard_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `leaderboard_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `leaderboard_ibfk_3` FOREIGN KEY (`author_id`) REFERENCES `member` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `message`
--
ALTER TABLE `message`
  ADD CONSTRAINT `message_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `member` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `message_ibfk_3` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD CONSTRAINT `reactionmenu_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `reactionmenu_option`
--
ALTER TABLE `reactionmenu_option`
  ADD CONSTRAINT `reactionmenu_option_ibfk_2` FOREIGN KEY (`message_id`) REFERENCES `reactionmenu_section_option` (`message_id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `reactionmenu_section`
--
ALTER TABLE `reactionmenu_section`
  ADD CONSTRAINT `reactionmenu_section_ibfk_1` FOREIGN KEY (`reactionmenu_id`) REFERENCES `reactionmenu` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `reactionmenu_section_option`
--
ALTER TABLE `reactionmenu_section_option`
  ADD CONSTRAINT `reactionmenu_section_option_ibfk_2` FOREIGN KEY (`section_id`) REFERENCES `reactionmenu_section` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
