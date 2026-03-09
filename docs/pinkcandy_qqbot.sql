-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- 主机： localhost
-- 生成日期： 2025-10-14 10:48:40
-- 服务器版本： 9.4.0-commercial
-- PHP 版本： 8.4.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 数据库： `pinkcandy_qqbot`
--

-- --------------------------------------------------------

--
-- 表的结构 `abbreviation_dictionary`
--

CREATE TABLE `abbreviation_dictionary` (
  `Id` int NOT NULL,
  `word` varchar(128) COLLATE utf8mb4_general_ci NOT NULL,
  `explanation` varchar(1024) COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- 表的结构 `date_reminder`
--

CREATE TABLE `date_reminder` (
  `title` varchar(128) COLLATE utf8mb4_general_ci NOT NULL,
  `date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- 表的结构 `group_chat_memories`
--

CREATE TABLE `group_chat_memories` (
  `session_id` varchar(128) COLLATE utf8mb4_general_ci NOT NULL,
  `history_json` json NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- 表的结构 `private_chat_memories`
--

CREATE TABLE `private_chat_memories` (
  `session_id` varchar(128) COLLATE utf8mb4_general_ci NOT NULL,
  `history_json` json NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- 表的结构 `schedule_messages`
--

CREATE TABLE `schedule_messages` (
  `Id` int NOT NULL,
  `time` datetime NOT NULL,
  `message` varchar(1024) COLLATE utf8mb4_general_ci NOT NULL,
  `groupid` varchar(128) COLLATE utf8mb4_general_ci NOT NULL,
  `isloop` int NOT NULL,
  `looptime` int NOT NULL,
  `addtime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- 表的结构 `private_chat_user_memories`
--

CREATE TABLE `private_chat_user_memories`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT 'QQ号',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '对方昵称',
  `memory` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '机器人记忆',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

--
-- 转储表的索引
--

--
-- 表的索引 `abbreviation_dictionary`
--
ALTER TABLE `abbreviation_dictionary`
  ADD PRIMARY KEY (`Id`);

--
-- 表的索引 `date_reminder`
--
ALTER TABLE `date_reminder`
  ADD PRIMARY KEY (`title`);

--
-- 表的索引 `group_chat_memories`
--
ALTER TABLE `group_chat_memories`
  ADD PRIMARY KEY (`session_id`);

--
-- 表的索引 `private_chat_memories`
--
ALTER TABLE `private_chat_memories`
  ADD PRIMARY KEY (`session_id`);

--
-- 表的索引 `schedule_messages`
--
ALTER TABLE `schedule_messages`
  ADD PRIMARY KEY (`Id`);

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `abbreviation_dictionary`
--
ALTER TABLE `abbreviation_dictionary`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `schedule_messages`
--
ALTER TABLE `schedule_messages`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
