-- phpMyAdmin SQL Dump
-- version 4.8.5
-- https://www.phpmyadmin.net/
--
-- Hostiteľ: 127.0.0.1:3306
-- Čas generovania: Pi 02.Aug 2019, 17:59
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
-- Databáza: `discord`
--

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `backup_attachemnts`
--

DROP TABLE IF EXISTS `backup_attachemnts`;
CREATE TABLE IF NOT EXISTS `backup_attachemnts` (
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  `size` int(11) NOT NULL,
  `filename` text COLLATE utf8_czech_ci NOT NULL,
  `url` varchar(1000) COLLATE utf8_czech_ci NOT NULL,
  UNIQUE KEY `url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `channels`
--

DROP TABLE IF EXISTS `channels`;
CREATE TABLE IF NOT EXISTS `channels` (
  `guild_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `name` text COLLATE utf8_czech_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UNIQUE` (`guild_id`,`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `guilds`
--

DROP TABLE IF EXISTS `guilds`;
CREATE TABLE IF NOT EXISTS `guilds` (
  `id` bigint(22) NOT NULL,
  `name` text COLLATE utf8_czech_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `leaderboard`
--

DROP TABLE IF EXISTS `leaderboard`;
CREATE TABLE IF NOT EXISTS `leaderboard` (
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `author_id` bigint(22) NOT NULL,
  `messages_sent` int(11) NOT NULL,
  `timestamp` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`guild_id`,`channel_id`,`author_id`) USING BTREE,
  KEY `channel_id` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `members`
--

DROP TABLE IF EXISTS `members`;
CREATE TABLE IF NOT EXISTS `members` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8_czech_ci NOT NULL,
  `nickname` varchar(127) COLLATE utf8_czech_ci NOT NULL,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `UNIQUE NAME` (`id`,`name`,`nickname`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu`
--

DROP TABLE IF EXISTS `reactionmenu`;
CREATE TABLE IF NOT EXISTS `reactionmenu` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8_czech_ci NOT NULL,
  PRIMARY KEY (`id`,`guild_id`,`channel_id`,`name`) USING BTREE,
  KEY `guild_id` (`guild_id`),
  KEY `channel_id` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_option`
--

DROP TABLE IF EXISTS `reactionmenu_option`;
CREATE TABLE IF NOT EXISTS `reactionmenu_option` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` bigint(22) NOT NULL,
  `emoji` text COLLATE utf8_czech_ci NOT NULL,
  `text` text COLLATE utf8_czech_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

--
-- Spúšťače `reactionmenu_option`
--
DROP TRIGGER IF EXISTS `update_options_count`;
DELIMITER $$
CREATE TRIGGER `update_options_count` AFTER INSERT ON `reactionmenu_option` FOR EACH ROW UPDATE `reactionmenu_section` AS sec SET `options`=(SELECT COUNT(*) FROM `reactionmenu_section_option` AS rel INNER JOIN reactionmenu_option AS opt ON rel.message_id = opt.message_id WHERE rel.section_id = sec.id) WHERE 1
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_section`
--

DROP TABLE IF EXISTS `reactionmenu_section`;
CREATE TABLE IF NOT EXISTS `reactionmenu_section` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reactionmenu_id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `options` int(11) NOT NULL DEFAULT '0',
  `text` varchar(12) COLLATE utf8_czech_ci NOT NULL,
  PRIMARY KEY (`id`,`reactionmenu_id`,`text`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_section_option`
--

DROP TABLE IF EXISTS `reactionmenu_section_option`;
CREATE TABLE IF NOT EXISTS `reactionmenu_section_option` (
  `section_id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `order_id` int(11) NOT NULL AUTO_INCREMENT,
  `is_full` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`section_id`,`order_id`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `verification`
--

DROP TABLE IF EXISTS `verification`;
CREATE TABLE IF NOT EXISTS `verification` (
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  PRIMARY KEY (`guild_id`,`channel_id`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

--
-- Obmedzenie pre exportované tabuľky
--

--
-- Obmedzenie pre tabuľku `channels`
--
ALTER TABLE `channels`
  ADD CONSTRAINT `channels_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guilds` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD CONSTRAINT `leaderboard_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guilds` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `leaderboard_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channels` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

--
-- Obmedzenie pre tabuľku `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD CONSTRAINT `reactionmenu_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guilds` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `reactionmenu_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channels` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
