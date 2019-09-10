-- phpMyAdmin SQL Dump
-- version 4.9.0.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Sep 10, 2019 at 09:13 PM
-- Server version: 8.0.17
-- PHP Version: 7.3.9

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `discordv1.1`
--

-- --------------------------------------------------------

--
-- Table structure for table `aboutmenu`
--

CREATE TABLE `aboutmenu` (
  `id` int(11) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `image` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `text` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `aboutmenu_options`
--

CREATE TABLE `aboutmenu_options` (
  `menu_id` int(11) NOT NULL,
  `id` int(11) NOT NULL,
  `emoji` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role_id` bigint(22) NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `attachment`
--

CREATE TABLE `attachment` (
  `message_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `filename` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `category`
--

CREATE TABLE `category` (
  `guild_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `name` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `position` int(11) NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `channel`
--

CREATE TABLE `channel` (
  `guild_id` bigint(22) NOT NULL,
  `category_id` bigint(22) DEFAULT '0',
  `id` bigint(22) NOT NULL,
  `name` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `position` int(11) NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `guild`
--

CREATE TABLE `guild` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `icon_url` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'https://dummyimage.com/600x600/36393f/ffffff.png&text=+',
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `leaderboard`
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
-- Table structure for table `leaderboard_emoji`
--

CREATE TABLE `leaderboard_emoji` (
  `guild_id` bigint(22) NOT NULL,
  `channel_id` bigint(22) NOT NULL,
  `emoji` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `sent_times` int(11) NOT NULL,
  `timestamp` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `logger`
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
-- Table structure for table `member`
--

CREATE TABLE `member` (
  `id` bigint(22) NOT NULL,
  `name` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `avatar_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `message`
--

CREATE TABLE `message` (
  `channel_id` bigint(22) NOT NULL,
  `author_id` bigint(22) NOT NULL,
  `id` bigint(22) NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_at` timestamp NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reactionmenu`
--

CREATE TABLE `reactionmenu` (
  `channel_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `rep_category_id` bigint(22) NOT NULL,
  `name` varchar(127) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reactionmenu_messages`
--

CREATE TABLE `reactionmenu_messages` (
  `reactionmenu_message_id` bigint(22) NOT NULL,
  `message_id` bigint(22) NOT NULL,
  `is_full` tinyint(1) NOT NULL DEFAULT '0',
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reactionmenu_options`
--

CREATE TABLE `reactionmenu_options` (
  `message_id` bigint(22) NOT NULL,
  `rep_channel_id` bigint(22) DEFAULT NULL,
  `emoji` varchar(127) COLLATE utf8mb4_unicode_ci NOT NULL,
  `text` varchar(127) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `verification`
--

CREATE TABLE `verification` (
  `channel_id` bigint(22) NOT NULL,
  `verified_role_id` bigint(22) NOT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `aboutmenu`
--
ALTER TABLE `aboutmenu`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `UNIQUE` (`channel_id`,`text`,`deleted_at`),
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `aboutmenu_ibfk_2` (`message_id`),
  ADD KEY `deleted_at` (`deleted_at`);

--
-- Indexes for table `aboutmenu_options`
--
ALTER TABLE `aboutmenu_options`
  ADD PRIMARY KEY (`id`),
  ADD KEY `menu_id` (`menu_id`),
  ADD KEY `deleted_at` (`deleted_at`);

--
-- Indexes for table `attachment`
--
ALTER TABLE `attachment`
  ADD PRIMARY KEY (`id`),
  ADD KEY `message_id` (`message_id`);

--
-- Indexes for table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `position` (`guild_id`,`position`,`deleted_at`) USING BTREE;

--
-- Indexes for table `channel`
--
ALTER TABLE `channel`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `position` (`guild_id`,`category_id`,`position`,`deleted_at`) USING BTREE,
  ADD KEY `channel_ibfk_1` (`category_id`);

--
-- Indexes for table `guild`
--
ALTER TABLE `guild`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique` (`id`,`deleted_at`) USING BTREE;

--
-- Indexes for table `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD PRIMARY KEY (`guild_id`,`channel_id`,`author_id`) USING BTREE,
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `author_id` (`author_id`);

--
-- Indexes for table `leaderboard_emoji`
--
ALTER TABLE `leaderboard_emoji`
  ADD PRIMARY KEY (`guild_id`,`channel_id`,`emoji`) USING BTREE,
  ADD KEY `channel_id` (`channel_id`),
  ADD KEY `author_id` (`emoji`);

--
-- Indexes for table `logger`
--
ALTER TABLE `logger`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `member`
--
ALTER TABLE `member`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique` (`id`,`deleted_at`) USING BTREE;

--
-- Indexes for table `message`
--
ALTER TABLE `message`
  ADD PRIMARY KEY (`id`) USING BTREE,
  ADD UNIQUE KEY `unique` (`channel_id`,`deleted_at`) USING BTREE,
  ADD KEY `message_ibfk_2` (`author_id`);

--
-- Indexes for table `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD UNIQUE KEY `UNIQUE` (`channel_id`,`name`,`deleted_at`) USING BTREE,
  ADD KEY `message_id` (`message_id`),
  ADD KEY `rep_category_id` (`rep_category_id`),
  ADD KEY `channel_id` (`channel_id`) USING BTREE;

--
-- Indexes for table `reactionmenu_messages`
--
ALTER TABLE `reactionmenu_messages`
  ADD UNIQUE KEY `UNIQUE` (`reactionmenu_message_id`,`message_id`,`deleted_at`),
  ADD KEY `message_id` (`message_id`);

--
-- Indexes for table `reactionmenu_options`
--
ALTER TABLE `reactionmenu_options`
  ADD UNIQUE KEY `UNIQUE` (`text`,`deleted_at`,`message_id`) USING BTREE,
  ADD KEY `reactionmenu_options_ibfk_1` (`message_id`);

--
-- Indexes for table `verification`
--
ALTER TABLE `verification`
  ADD UNIQUE KEY `UNIQUE` (`channel_id`,`deleted_at`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `aboutmenu`
--
ALTER TABLE `aboutmenu`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `aboutmenu_options`
--
ALTER TABLE `aboutmenu_options`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `logger`
--
ALTER TABLE `logger`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `aboutmenu_options`
--
ALTER TABLE `aboutmenu_options`
  ADD CONSTRAINT `aboutmenu_options_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `aboutmenu` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `aboutmenu_options_ibfk_2` FOREIGN KEY (`deleted_at`) REFERENCES `aboutmenu` (`deleted_at`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `attachment`
--
ALTER TABLE `attachment`
  ADD CONSTRAINT `attachment_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `category`
--
ALTER TABLE `category`
  ADD CONSTRAINT `category_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `channel`
--
ALTER TABLE `channel`
  ADD CONSTRAINT `channel_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `channel_ibfk_2` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD CONSTRAINT `leaderboard_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `leaderboard_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `leaderboard_emoji`
--
ALTER TABLE `leaderboard_emoji`
  ADD CONSTRAINT `leaderboard_emoji_ibfk_1` FOREIGN KEY (`guild_id`) REFERENCES `guild` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `leaderboard_emoji_ibfk_2` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `message`
--
ALTER TABLE `message`
  ADD CONSTRAINT `message_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `member` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `message_ibfk_3` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `reactionmenu`
--
ALTER TABLE `reactionmenu`
  ADD CONSTRAINT `reactionmenu_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `reactionmenu_messages`
--
ALTER TABLE `reactionmenu_messages`
  ADD CONSTRAINT `reactionmenu_messages_ibfk_1` FOREIGN KEY (`reactionmenu_message_id`) REFERENCES `reactionmenu` (`message_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `reactionmenu_options`
--
ALTER TABLE `reactionmenu_options`
  ADD CONSTRAINT `reactionmenu_options_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `reactionmenu_messages` (`message_id`) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Constraints for table `verification`
--
ALTER TABLE `verification`
  ADD CONSTRAINT `verification_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
