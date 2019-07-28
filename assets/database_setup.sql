-- phpMyAdmin SQL Dump
-- version 4.8.5
-- https://www.phpmyadmin.net/
--
-- Hostiteľ: 127.0.0.1:3306
-- Čas generovania: Ne 28.Júl 2019, 08:20
-- Verzia serveru: 5.7.26
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
  `guild` text COLLATE utf8_czech_ci NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `channel` text COLLATE utf8_czech_ci NOT NULL,
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
-- Štruktúra tabuľky pre tabuľku `leaderbaord`
--

DROP TABLE IF EXISTS `leaderbaord`;
CREATE TABLE IF NOT EXISTS `leaderbaord` (
  `guild_id` bigint(22) NOT NULL,
  `guild` text COLLATE utf8_czech_ci NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `channel` text COLLATE utf8_czech_ci NOT NULL,
  `author_id` bigint(22) NOT NULL,
  `author` text COLLATE utf8_czech_ci NOT NULL,
  `messages_sent` int(11) NOT NULL,
  UNIQUE KEY `guild_id` (`guild_id`,`channel_id`,`author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci;

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
  PRIMARY KEY (`id`,`guild_id`,`channel_id`,`name`) USING BTREE
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
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
