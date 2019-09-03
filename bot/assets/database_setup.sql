-- phpMyAdmin SQL Dump
-- version 4.9.0.1
-- https://www.phpmyadmin.net/
--
-- Hostiteľ: localhost
-- Čas generovania: Út 03.Sep 2019, 13:52
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
-- Štruktúra tabuľky pre tabuľku `aboutmenu`
--

CREATE TABLE `aboutmenu` (
  `id` int(11) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `image` text COLLATE utf8mb4_general_ci NOT NULL,
  `text` text COLLATE utf8mb4_general_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `aboutmenu_options`
--

CREATE TABLE `aboutmenu_options` (
  `menu_id` int(11) NOT NULL,
  `id` int(11) NOT NULL,
  `emoji` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `deleted_at` timestamp NULL DEFAULT NULL
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
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `guild`
--

CREATE TABLE `guild` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `icon_url` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://dummyimage.com/600x600/36393f/ffffff.png&text=+',
  `deleted_at` timestamp NULL DEFAULT NULL
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `leaderboard_emoji`
--

CREATE TABLE `leaderboard_emoji` (
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `emoji` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `sent_times` int(11) NOT NULL,
  `timestamp` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `logger`
--

CREATE TABLE `logger` (
  `id` int(11) NOT NULL,
  `from_date` timestamp NULL DEFAULT NULL,
  `to_date` timestamp NULL DEFAULT NULL,
  `state` enum('failed','running','success') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'failed',
  `finished_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `member`
--

CREATE TABLE `member` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_general_ci NOT NULL,
  `avatar_url` text COLLATE utf8mb4_general_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
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
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu`
--

CREATE TABLE `reactionmenu` (
  `id` int(11) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `sections` int(11) NOT NULL DEFAULT '0',
  `name` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_option`
--

CREATE TABLE `reactionmenu_option` (
  `id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `emoji` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `text` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `rep_channel_id` bigint(22) NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Spúšťače `reactionmenu_option`
--
DELIMITER $$
CREATE TRIGGER `update_sec_opt_options_count_insert` AFTER INSERT ON `reactionmenu_option` FOR EACH ROW UPDATE `reactionmenu_section_option` AS sec_opt SET `options`=(SELECT COUNT(*) FROM `reactionmenu_option` AS opt WHERE opt.message_id = sec_opt.message_id AND opt.deleted_at IS NULL)  WHERE sec_opt.message_id = NEW.message_id
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `update_sec_opt_options_count_update` AFTER UPDATE ON `reactionmenu_option` FOR EACH ROW UPDATE `reactionmenu_section_option` AS sec_opt SET `options`=(SELECT COUNT(*) FROM `reactionmenu_option` AS opt WHERE opt.message_id = sec_opt.message_id AND opt.deleted_at IS NULL) WHERE sec_opt.message_id = NEW.message_id
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `update_section_options_count_insert` AFTER INSERT ON `reactionmenu_option` FOR EACH ROW UPDATE `reactionmenu_section` AS sec SET `options`=(SELECT COUNT(*) FROM `reactionmenu_section_option` AS rel INNER JOIN reactionmenu_option AS opt ON rel.message_id = opt.message_id WHERE rel.section_id = sec.id) 
WHERE sec.id = (SELECT section_id 
                FROM `reactionmenu_section_option` AS rel 
        		WHERE rel.message_id = NEW.message_id)
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `update_section_options_count_update` AFTER UPDATE ON `reactionmenu_option` FOR EACH ROW UPDATE `reactionmenu_section` AS sec 
SET `options`= 
    (SELECT COUNT(*) 
     FROM `reactionmenu_section_option` AS rel 
     INNER JOIN reactionmenu_option AS opt 
     USING (message_id) 
     WHERE rel.section_id = sec.id)  

WHERE sec.id = (SELECT section_id 
                FROM `reactionmenu_section_option` AS rel 
        		WHERE rel.message_id = NEW.message_id)
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
  `text` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `rep_category_id` bigint(22) NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Spúšťače `reactionmenu_section`
--
DELIMITER $$
CREATE TRIGGER `update_sections_count` AFTER INSERT ON `reactionmenu_section` FOR EACH ROW UPDATE `reactionmenu` AS menu SET `sections`=(SELECT COUNT(*) FROM `reactionmenu_section` AS sec WHERE sec.reactionmenu_id = menu.id)
WHERE menu.id = NEW.reactionmenu_id
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Štruktúra tabuľky pre tabuľku `reactionmenu_section_option`
--

CREATE TABLE `reactionmenu_section_option` (
  `section_id` int(11) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `order_id` int(11) NOT NULL,
  `options` int(11) NOT NULL DEFAULT '0',
  `is_full` tinyint(1) NOT NULL DEFAULT '0',
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Kľúče pre exportované tabuľky
--

--
-- Indexy pre tabuľku `aboutmenu`
--
ALTER TABLE `aboutmenu`
  ADD PRIMARY KEY (`id`),
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `aboutmenu_ibfk_2` (`message_id`);

--
-- Indexy pre tabuľku `aboutmenu_options`
--
ALTER TABLE `aboutmenu_options`
  ADD PRIMARY KEY (`id`),
  ADD KEY `menu_id` (`menu_id`);

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
  ADD UNIQUE KEY `position` (`guild_id`,`position`,`deleted_at`) USING BTREE;

--
-- Indexy pre tabuľku `channel`
--
ALTER TABLE `channel`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `position` (`guild_id`,`category_id`,`position`,`deleted_at`) USING BTREE,
  ADD KEY `channel_ibfk_1` (`category_id`);

--
-- Indexy pre tabuľku `guild`
--
ALTER TABLE `guild`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique` (`id`,`deleted_at`) USING BTREE;

--
-- Indexy pre tabuľku `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD PRIMARY KEY (`guild_id`,`channel_id`,`author_id`) USING BTREE,
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `author_id` (`author_id`);

--
-- Indexy pre tabuľku `leaderboard_emoji`
--
ALTER TABLE `leaderboard_emoji`
  ADD PRIMARY KEY (`guild_id`,`channel_id`,`emoji`) USING BTREE,
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `author_id` (`emoji`);

--
-- Indexy pre tabuľku `logger`
--
ALTER TABLE `logger`
  ADD PRIMARY KEY (`id`);

--
-- Indexy pre tabuľku `member`
--
ALTER TABLE `member`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique` (`id`,`deleted_at`) USING BTREE;

--
-- Indexy pre tabuľku `message`
--
ALTER TABLE `message`
  ADD PRIMARY KEY (`id`) USING BTREE,
  ADD UNIQUE KEY `unique` (`channel_id`,`deleted_at`) USING BTREE,
  ADD KEY `message_ibfk_2` (`author_id`);

--
-- Indexy pre tabuľku `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD PRIMARY KEY (`id`) USING BTREE,
  ADD UNIQUE KEY `unique` (`channel_id`,`name`,`deleted_at`) USING BTREE,
  ADD KEY `reactionmenu_ibfk_2` (`message_id`);

--
-- Indexy pre tabuľku `reactionmenu_option`
--
ALTER TABLE `reactionmenu_option`
  ADD PRIMARY KEY (`id`),
  ADD KEY `message_id` (`message_id`),
  ADD KEY `rep_channel_id` (`rep_channel_id`);

--
-- Indexy pre tabuľku `reactionmenu_section`
--
ALTER TABLE `reactionmenu_section`
  ADD PRIMARY KEY (`id`) USING BTREE,
  ADD UNIQUE KEY `unique` (`reactionmenu_id`,`text`,`deleted_at`) USING BTREE,
  ADD KEY `reactionmenu_section_ibfk_1` (`reactionmenu_id`),
  ADD KEY `section_id` (`rep_category_id`),
  ADD KEY `reactionmenu_section_ibfk_3` (`message_id`);

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
-- AUTO_INCREMENT pre tabuľku `aboutmenu`
--
ALTER TABLE `aboutmenu`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pre tabuľku `aboutmenu_options`
--
ALTER TABLE `aboutmenu_options`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pre tabuľku `logger`
--
ALTER TABLE `logger`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

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
-- Obmedzenie pre tabuľku `aboutmenu`
--
ALTER TABLE `aboutmenu`
  ADD CONSTRAINT `aboutmenu_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `aboutmenu_ibfk_2` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `aboutmenu_options`
--
ALTER TABLE `aboutmenu_options`
  ADD CONSTRAINT `aboutmenu_options_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `aboutmenu` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `attachment`
--
ALTER TABLE `attachment`
  ADD CONSTRAINT `attachment_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `category`
--
ALTER TABLE `category`
  ADD CONSTRAINT `category_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `channel`
--
ALTER TABLE `channel`
  ADD CONSTRAINT `channel_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `channel_ibfk_2` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD CONSTRAINT `leaderboard_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `leaderboard_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `leaderboard_ibfk_3` FOREIGN KEY (`author_id`) REFERENCES `member` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `leaderboard_emoji`
--
ALTER TABLE `leaderboard_emoji`
  ADD CONSTRAINT `leaderboard_emoji_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `leaderboard_emoji_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `message`
--
ALTER TABLE `message`
  ADD CONSTRAINT `message_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `member` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `message_ibfk_3` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD CONSTRAINT `reactionmenu_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `reactionmenu_ibfk_2` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `reactionmenu_option`
--
ALTER TABLE `reactionmenu_option`
  ADD CONSTRAINT `reactionmenu_option_ibfk_2` FOREIGN KEY (`message_id`) REFERENCES `reactionmenu_section_option` (`message_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `reactionmenu_option_ibfk_3` FOREIGN KEY (`rep_channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `reactionmenu_section`
--
ALTER TABLE `reactionmenu_section`
  ADD CONSTRAINT `reactionmenu_section_ibfk_1` FOREIGN KEY (`reactionmenu_id`) REFERENCES `reactionmenu` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `reactionmenu_section_ibfk_2` FOREIGN KEY (`rep_category_id`) REFERENCES `category` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `reactionmenu_section_ibfk_3` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Obmedzenie pre tabuľku `reactionmenu_section_option`
--
ALTER TABLE `reactionmenu_section_option`
  ADD CONSTRAINT `reactionmenu_section_option_ibfk_2` FOREIGN KEY (`section_id`) REFERENCES `reactionmenu_section` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `reactionmenu_section_option_ibfk_3` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
