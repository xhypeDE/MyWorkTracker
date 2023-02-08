CREATE TABLE `o_groups` (
  `o_ID` int(9) NOT NULL AUTO_INCREMENT,
  `o_name` varchar(64) NOT NULL,
  `o_package` int(3) NOT NULL,
  `o_restricted` tinyint(1) NOT NULL,
  PRIMARY KEY (`o_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `o_groups` (`o_ID`, `o_name`, `o_package`, `o_restricted`) VALUES ('40', 'Schmidt Schmiede AG', '0', '0');
INSERT INTO `o_groups` (`o_ID`, `o_name`, `o_package`, `o_restricted`) VALUES ('41', 'Masteradmins', '0', '0');
INSERT INTO `o_groups` (`o_ID`, `o_name`, `o_package`, `o_restricted`) VALUES ('42', 'Master Online Marketing', '0', '0');

CREATE TABLE `o_invites` (
  `invite_id` int(11) NOT NULL AUTO_INCREMENT,
  `invite_code` varchar(64) NOT NULL,
  `invader_name` varchar(64) NOT NULL,
  `status` tinyint(1) DEFAULT NULL,
  `admin_level` int(11) NOT NULL,
  `invite_o_id` int(11) NOT NULL,
  PRIMARY KEY (`invite_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `o_invites` (`invite_id`, `invite_code`, `invader_name`, `status`, `admin_level`,
                         `invite_o_id`) VALUES (NULL, '5MWVZV8A', 'Berhard Schmidt', '1', '1', '40');

CREATE TABLE `users` (
  `u_ID` int(6) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `surname` varchar(64) NOT NULL,
  `phone` varchar(32) NOT NULL,
  `email` varchar(128) NOT NULL,
  `password` text NOT NULL,
  `hourly_rate` varchar(32) DEFAULT NULL,
  `workload` varchar(32) DEFAULT NULL,
  `admin_level` int(11) NOT NULL,
  `status` varchar(32) DEFAULT NULL,
  `is_verified` tinyint(1) NOT NULL,
  `verification_code` varchar(128) NOT NULL,
  `o_ID` int(11) NOT NULL,
  PRIMARY KEY (`u_ID`),
  KEY `o_ID` (`o_ID`),
  CONSTRAINT `o_ID fremd` FOREIGN KEY (`o_ID`) REFERENCES `o_groups` (`o_ID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `users` (`u_ID`, `name`, `surname`, `phone`, `email`, `password`, `hourly_rate`, `workload`,
                     `admin_level`, `status`, `is_verified`, `verification_code`, `o_ID`)
                      VALUES (NULL, 'Masteradmin', 'myWorkTracker', '+49000000000', 'masteradmin@myworktracker.de',
                              '$pbkdf2-sha256$29000$QmhtLWWs1dp7r9W6l1KKkQ$V10HEcdbP.yGo0z23Hgp7e.ZCh8OqAo/7y3TRORA7Zg',
                              NULL, NULL, '3', 'offline', '0', 'OUE773PN', '41');

INSERT INTO `users` (`u_ID`, `name`, `surname`, `phone`, `email`, `password`, `hourly_rate`, `workload`,
                     `admin_level`, `status`, `is_verified`, `verification_code`, `o_ID`)
                     VALUES (NULL, 'Gralf', 'Hesse', '+491516154562', 'g.hesse@schmidt-schmiede.de',
                             '$pbkdf2-sha256$29000$/r.3NkbIeU9J6T3HuDdGiA$G9cAkaYxFaazGAVG3ZIyyORcXmljAAKpUdOIkzz22OQ',
                             '19.50', '40', '1', 'offline', '0', '32ZC39N9', '40');

INSERT INTO `users` (`u_ID`, `name`, `surname`, `phone`, `email`, `password`, `hourly_rate`, `workload`,
                     `admin_level`, `status`, `is_verified`, `verification_code`, `o_ID`)
                     VALUES (NULL, 'Heike', 'Binder', '+491512514265', 'h.binder@schmidt-schmiede.de',
                             '$pbkdf2-sha256$29000$MiYk5Nz733tvbU2JkbKW0g$DXmQyJunD5cNcVQlFU2uvDkfcbuU5oUOdy0bqzdaNN0',
                             '19.50', '40', '1', 'offline', '0', 'SQTK4WKH', '40');

CREATE TABLE `time_entries` (
  `t_ID` int(11) NOT NULL AUTO_INCREMENT,
  `date_a` datetime NOT NULL,
  `date_b` datetime DEFAULT NULL,
  `diff_time` int(11) DEFAULT NULL,
  `pause_date_a` datetime DEFAULT NULL,
  `pause_date_b` datetime DEFAULT NULL,
  `pause` int(11) DEFAULT NULL,
  `tracking` tinyint(1) DEFAULT NULL,
  `tracking_pause` tinyint(1) DEFAULT NULL,
  `actual_diff_time` int(11) DEFAULT NULL,
  `u_ID` int(11) NOT NULL,
  `o_ID` int(11) NOT NULL,
  PRIMARY KEY (`t_ID`),
  KEY `o_ID Fremd Time` (`o_ID`),
  KEY `u_ID Fremd Time` (`u_ID`),
  CONSTRAINT `o_ID Fremd Time` FOREIGN KEY (`o_ID`) REFERENCES `users` (`o_ID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `u_ID Fremd Time` FOREIGN KEY (`u_ID`) REFERENCES `users` (`u_ID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


INSERT INTO `time_entries` (`t_ID`, `date_a`, `date_b`, `diff_time`, `pause_date_a`, `pause_date_b`, `pause`,
                            `tracking`, `tracking_pause`, `actual_diff_time`, `u_ID`, `o_ID`)
                            VALUES (NULL, '2022-01-03 09:30:00', '2022-01-03 17:30:00', '28800', NULL, NULL,
                                    '2700', '0', '0', '26100', '58', '40');
