# 完整数据库表结构文档

本文档包含数据库中所有 36 个表的创建命令和字段说明。

## 目录

### Django 系统表

1. auth_group
2. auth_group_permissions
3. auth_permission
4. auth_user
5. auth_user_groups
6. auth_user_user_permissions
7. django_admin_log
8. django_content_type
9. django_migrations
10. django_session

### Heritage API 业务表

1. heritage_api_creationcomment
2. heritage_api_creationfavorite
3. heritage_api_creationlike
4. heritage_api_creationreport
5. heritage_api_creationshare
6. heritage_api_creationtag
7. heritage_api_creationviewhistory
8. heritage_api_forumannouncement
9. heritage_api_forumcomment
10. heritage_api_forumcommentlike
11. heritage_api_forumpost
12. heritage_api_forumpost_tags
13. heritage_api_forumpostfavorite
14. heritage_api_forumpostlike
15. heritage_api_forumreport
16. heritage_api_forumtag
17. heritage_api_forumuserfollow
18. heritage_api_forumuserstats
19. heritage_api_heritage
20. heritage_api_heritageimage
21. heritage_api_news
22. heritage_api_policy
23. heritage_api_usercreation
24. heritage_api_userfavorite
25. heritage_api_userhistory
26. heritage_api_userprofile

---

## auth_group

### 创建命令

`sql
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | int | NO |  | 主键, auto_increment |
| name | varchar(150) | NO |  | 唯一键 |

---

## auth_group_permissions

### 创建命令

`sql
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| group_id | int | NO |  | 索引 |
| permission_id | int | NO |  | 索引 |

---

## auth_permission

### 创建命令

`sql
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | int | NO |  | 主键, auto_increment |
| name | varchar(255) | NO |  |  |
| content_type_id | int | NO |  | 索引 |
| codename | varchar(100) | NO |  |  |

---

## auth_user

### 创建命令

`sql
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | int | NO |  | 主键, auto_increment |
| password | varchar(128) | NO |  |  |
| last_login | datetime(6) | YES |  |  |
| is_superuser | tinyint(1) | NO |  |  |
| username | varchar(150) | NO |  | 唯一键 |
| first_name | varchar(150) | NO |  |  |
| last_name | varchar(150) | NO |  |  |
| email | varchar(254) | NO |  |  |
| is_staff | tinyint(1) | NO |  |  |
| is_active | tinyint(1) | NO |  |  |
| date_joined | datetime(6) | NO |  |  |

---

## auth_user_groups

### 创建命令

`sql
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| user_id | int | NO |  | 索引 |
| group_id | int | NO |  | 索引 |

---

## auth_user_user_permissions

### 创建命令

`sql
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| user_id | int | NO |  | 索引 |
| permission_id | int | NO |  | 索引 |

---

## django_admin_log

### 创建命令

`sql
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | int | NO |  | 主键, auto_increment |
| action_time | datetime(6) | NO |  |  |
| object_id | longtext | YES |  |  |
| object_repr | varchar(200) | NO |  |  |
| action_flag | smallint unsigned | NO |  |  |
| change_message | longtext | NO |  |  |
| content_type_id | int | YES |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## django_content_type

### 创建命令

`sql
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | int | NO |  | 主键, auto_increment |
| app_label | varchar(100) | NO |  | 索引 |
| model | varchar(100) | NO |  |  |

---

## django_migrations

### 创建命令

`sql
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| app | varchar(255) | NO |  |  |
| name | varchar(255) | NO |  |  |
| applied | datetime(6) | NO |  |  |

---

## django_session

### 创建命令

`sql
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| session_key | varchar(40) | NO |  | 主键 |
| session_data | longtext | NO |  |  |
| expire_date | datetime(6) | NO |  | 索引 |

---

## heritage_api_creationcomment

### 创建命令

`sql
CREATE TABLE `heritage_api_creationcomment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `like_count` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `creation_id` bigint NOT NULL,
  `parent_id` bigint DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_api_creatio_creation_id_2b8684c6_fk_heritage_` (`creation_id`),
  KEY `heritage_api_creatio_parent_id_f3f954dd_fk_heritage_` (`parent_id`),
  KEY `heritage_api_creationcomment_user_id_82780950_fk_auth_user_id` (`user_id`),
  CONSTRAINT `heritage_api_creatio_creation_id_2b8684c6_fk_heritage_` FOREIGN KEY (`creation_id`) REFERENCES `heritage_api_usercreation` (`id`),
  CONSTRAINT `heritage_api_creatio_parent_id_f3f954dd_fk_heritage_` FOREIGN KEY (`parent_id`) REFERENCES `heritage_api_creationcomment` (`id`),
  CONSTRAINT `heritage_api_creationcomment_user_id_82780950_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_creationcomment_chk_1` CHECK ((`like_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| content | longtext | NO |  |  |
| is_active | tinyint(1) | NO |  |  |
| like_count | int unsigned | NO |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| creation_id | bigint | NO |  | 索引 |
| parent_id | bigint | YES |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_creationfavorite

### 创建命令

`sql
CREATE TABLE `heritage_api_creationfavorite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `creation_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_creationfavorite_user_id_creation_id_deaa700a_uniq` (`user_id`,`creation_id`),
  KEY `heritage_api_creatio_creation_id_dfae39a6_fk_heritage_` (`creation_id`),
  CONSTRAINT `heritage_api_creatio_creation_id_dfae39a6_fk_heritage_` FOREIGN KEY (`creation_id`) REFERENCES `heritage_api_usercreation` (`id`),
  CONSTRAINT `heritage_api_creationfavorite_user_id_186bf9d5_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| creation_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_creationlike

### 创建命令

`sql
CREATE TABLE `heritage_api_creationlike` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `creation_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_creationlike_user_id_creation_id_dbe3ce15_uniq` (`user_id`,`creation_id`),
  KEY `heritage_api_creatio_creation_id_3ddd5a54_fk_heritage_` (`creation_id`),
  CONSTRAINT `heritage_api_creatio_creation_id_3ddd5a54_fk_heritage_` FOREIGN KEY (`creation_id`) REFERENCES `heritage_api_usercreation` (`id`),
  CONSTRAINT `heritage_api_creationlike_user_id_3417cf4f_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| creation_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_creationreport

### 创建命令

`sql
CREATE TABLE `heritage_api_creationreport` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `report_type` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `evidence_urls` json NOT NULL,
  `handled_at` datetime(6) DEFAULT NULL,
  `resolution` longtext,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `creation_id` bigint NOT NULL,
  `handled_by_id` int DEFAULT NULL,
  `reporter_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_api_creatio_creation_id_a5a08eb1_fk_heritage_` (`creation_id`),
  KEY `heritage_api_creatio_handled_by_id_cc07b1ae_fk_auth_user` (`handled_by_id`),
  KEY `heritage_api_creationreport_reporter_id_1d864b60_fk_auth_user_id` (`reporter_id`),
  CONSTRAINT `heritage_api_creatio_creation_id_a5a08eb1_fk_heritage_` FOREIGN KEY (`creation_id`) REFERENCES `heritage_api_usercreation` (`id`),
  CONSTRAINT `heritage_api_creatio_handled_by_id_cc07b1ae_fk_auth_user` FOREIGN KEY (`handled_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_creationreport_reporter_id_1d864b60_fk_auth_user_id` FOREIGN KEY (`reporter_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| report_type | varchar(20) | NO |  |  |
| description | longtext | NO |  |  |
| status | varchar(20) | NO |  |  |
| evidence_urls | json | NO |  |  |
| handled_at | datetime(6) | YES |  |  |
| resolution | longtext | YES |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| creation_id | bigint | NO |  | 索引 |
| handled_by_id | int | YES |  | 索引 |
| reporter_id | int | NO |  | 索引 |

---

## heritage_api_creationshare

### 创建命令

`sql
CREATE TABLE `heritage_api_creationshare` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `platform` varchar(20) NOT NULL,
  `shared_at` datetime(6) NOT NULL,
  `creation_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_api_creatio_creation_id_6f199e89_fk_heritage_` (`creation_id`),
  KEY `heritage_api_creationshare_user_id_ac5206af_fk_auth_user_id` (`user_id`),
  CONSTRAINT `heritage_api_creatio_creation_id_6f199e89_fk_heritage_` FOREIGN KEY (`creation_id`) REFERENCES `heritage_api_usercreation` (`id`),
  CONSTRAINT `heritage_api_creationshare_user_id_ac5206af_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| platform | varchar(20) | NO |  |  |
| shared_at | datetime(6) | NO |  |  |
| creation_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_creationtag

### 创建命令

`sql
CREATE TABLE `heritage_api_creationtag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` longtext,
  `usage_count` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `heritage_api_creationtag_chk_1` CHECK ((`usage_count` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| name | varchar(50) | NO |  | 唯一键 |
| description | longtext | YES |  |  |
| usage_count | int unsigned | NO |  |  |
| is_active | tinyint(1) | NO |  |  |
| created_at | datetime(6) | NO |  |  |

---

## heritage_api_creationviewhistory

### 创建命令

`sql
CREATE TABLE `heritage_api_creationviewhistory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `viewed_at` datetime(6) NOT NULL,
  `duration` int unsigned NOT NULL,
  `creation_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_creationvie_user_id_creation_id_b798f1d1_uniq` (`user_id`,`creation_id`),
  KEY `heritage_api_creatio_creation_id_5f43dbaa_fk_heritage_` (`creation_id`),
  CONSTRAINT `heritage_api_creatio_creation_id_5f43dbaa_fk_heritage_` FOREIGN KEY (`creation_id`) REFERENCES `heritage_api_usercreation` (`id`),
  CONSTRAINT `heritage_api_creatio_user_id_e13d6b8e_fk_auth_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_creationviewhistory_chk_1` CHECK ((`duration` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| viewed_at | datetime(6) | NO |  |  |
| duration | int unsigned | NO |  |  |
| creation_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_forumannouncement

### 创建命令

`sql
CREATE TABLE `heritage_api_forumannouncement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `content` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_pinned` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_api_foruman_author_id_6b054c01_fk_auth_user` (`author_id`),
  CONSTRAINT `heritage_api_foruman_author_id_6b054c01_fk_auth_user` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| title | varchar(200) | NO |  |  |
| content | longtext | NO |  |  |
| is_active | tinyint(1) | NO |  |  |
| is_pinned | tinyint(1) | NO |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| author_id | int | NO |  | 索引 |

---

## heritage_api_forumcomment

### 创建命令

`sql
CREATE TABLE `heritage_api_forumcomment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `like_count` int unsigned NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` int NOT NULL,
  `parent_id` bigint DEFAULT NULL,
  `post_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_ap_post_id_037964_idx` (`post_id`,`created_at`),
  KEY `heritage_ap_parent__2949bd_idx` (`parent_id`),
  KEY `heritage_api_forumcomment_author_id_9310be6a_fk_auth_user_id` (`author_id`),
  CONSTRAINT `heritage_api_forumco_parent_id_77e55104_fk_heritage_` FOREIGN KEY (`parent_id`) REFERENCES `heritage_api_forumcomment` (`id`),
  CONSTRAINT `heritage_api_forumco_post_id_fb66e7aa_fk_heritage_` FOREIGN KEY (`post_id`) REFERENCES `heritage_api_forumpost` (`id`),
  CONSTRAINT `heritage_api_forumcomment_author_id_9310be6a_fk_auth_user_id` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_forumcomment_chk_1` CHECK ((`like_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| content | longtext | NO |  |  |
| like_count | int unsigned | NO |  |  |
| is_deleted | tinyint(1) | NO |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| author_id | int | NO |  | 索引 |
| parent_id | bigint | YES |  | 索引 |
| post_id | bigint | NO |  | 索引 |

---

## heritage_api_forumcommentlike

### 创建命令

`sql
CREATE TABLE `heritage_api_forumcommentlike` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `comment_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_forumcommentlike_user_id_comment_id_c31e12b2_uniq` (`user_id`,`comment_id`),
  KEY `heritage_api_forumco_comment_id_25e5a8dd_fk_heritage_` (`comment_id`),
  CONSTRAINT `heritage_api_forumco_comment_id_25e5a8dd_fk_heritage_` FOREIGN KEY (`comment_id`) REFERENCES `heritage_api_forumcomment` (`id`),
  CONSTRAINT `heritage_api_forumcommentlike_user_id_afef0a4e_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| comment_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_forumpost

### 创建命令

`sql
CREATE TABLE `heritage_api_forumpost` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `content` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `is_pinned` tinyint(1) NOT NULL,
  `is_featured` tinyint(1) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `view_count` int unsigned NOT NULL,
  `like_count` int unsigned NOT NULL,
  `comment_count` int unsigned NOT NULL,
  `favorite_count` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `last_reply_at` datetime(6) DEFAULT NULL,
  `author_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_ap_created_83946d_idx` (`created_at` DESC),
  KEY `heritage_ap_last_re_a082dd_idx` (`last_reply_at` DESC),
  KEY `heritage_ap_is_pinn_3848a2_idx` (`is_pinned`,`last_reply_at` DESC),
  KEY `heritage_ap_status_af6fb7_idx` (`status`),
  KEY `heritage_api_forumpost_author_id_eb962c3b_fk_auth_user_id` (`author_id`),
  CONSTRAINT `heritage_api_forumpost_author_id_eb962c3b_fk_auth_user_id` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_forumpost_chk_1` CHECK ((`view_count` >= 0)),
  CONSTRAINT `heritage_api_forumpost_chk_2` CHECK ((`like_count` >= 0)),
  CONSTRAINT `heritage_api_forumpost_chk_3` CHECK ((`comment_count` >= 0)),
  CONSTRAINT `heritage_api_forumpost_chk_4` CHECK ((`favorite_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| title | varchar(200) | NO |  |  |
| content | longtext | NO |  |  |
| status | varchar(20) | NO |  | 索引 |
| is_pinned | tinyint(1) | NO |  | 索引 |
| is_featured | tinyint(1) | NO |  |  |
| is_locked | tinyint(1) | NO |  |  |
| view_count | int unsigned | NO |  |  |
| like_count | int unsigned | NO |  |  |
| comment_count | int unsigned | NO |  |  |
| favorite_count | int unsigned | NO |  |  |
| created_at | datetime(6) | NO |  | 索引 |
| updated_at | datetime(6) | NO |  |  |
| last_reply_at | datetime(6) | YES |  | 索引 |
| author_id | int | NO |  | 索引 |

---

## heritage_api_forumpost_tags

### 创建命令

`sql
CREATE TABLE `heritage_api_forumpost_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `forumpost_id` bigint NOT NULL,
  `forumtag_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_forumpost_t_forumpost_id_forumtag_id_274c7456_uniq` (`forumpost_id`,`forumtag_id`),
  KEY `heritage_api_forumpo_forumtag_id_aa23e57a_fk_heritage_` (`forumtag_id`),
  CONSTRAINT `heritage_api_forumpo_forumpost_id_0f0c63c0_fk_heritage_` FOREIGN KEY (`forumpost_id`) REFERENCES `heritage_api_forumpost` (`id`),
  CONSTRAINT `heritage_api_forumpo_forumtag_id_aa23e57a_fk_heritage_` FOREIGN KEY (`forumtag_id`) REFERENCES `heritage_api_forumtag` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| forumpost_id | bigint | NO |  | 索引 |
| forumtag_id | bigint | NO |  | 索引 |

---

## heritage_api_forumpostfavorite

### 创建命令

`sql
CREATE TABLE `heritage_api_forumpostfavorite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_forumpostfavorite_user_id_post_id_19b5692c_uniq` (`user_id`,`post_id`),
  KEY `heritage_api_forumpo_post_id_50c97828_fk_heritage_` (`post_id`),
  CONSTRAINT `heritage_api_forumpo_post_id_50c97828_fk_heritage_` FOREIGN KEY (`post_id`) REFERENCES `heritage_api_forumpost` (`id`),
  CONSTRAINT `heritage_api_forumpostfavorite_user_id_d1975695_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| post_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_forumpostlike

### 创建命令

`sql
CREATE TABLE `heritage_api_forumpostlike` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_forumpostlike_user_id_post_id_45446a27_uniq` (`user_id`,`post_id`),
  KEY `heritage_api_forumpo_post_id_671d73a5_fk_heritage_` (`post_id`),
  CONSTRAINT `heritage_api_forumpo_post_id_671d73a5_fk_heritage_` FOREIGN KEY (`post_id`) REFERENCES `heritage_api_forumpost` (`id`),
  CONSTRAINT `heritage_api_forumpostlike_user_id_106e3a4b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| post_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_forumreport

### 创建命令

`sql
CREATE TABLE `heritage_api_forumreport` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reason` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `handler_note` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `handled_at` datetime(6) DEFAULT NULL,
  `comment_id` bigint DEFAULT NULL,
  `handler_id` int DEFAULT NULL,
  `post_id` bigint DEFAULT NULL,
  `reporter_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_api_forumre_comment_id_46ce4908_fk_heritage_` (`comment_id`),
  KEY `heritage_api_forumreport_handler_id_c1965bd9_fk_auth_user_id` (`handler_id`),
  KEY `heritage_api_forumre_post_id_8f11184b_fk_heritage_` (`post_id`),
  KEY `heritage_api_forumreport_reporter_id_39ffaa79_fk_auth_user_id` (`reporter_id`),
  CONSTRAINT `heritage_api_forumre_comment_id_46ce4908_fk_heritage_` FOREIGN KEY (`comment_id`) REFERENCES `heritage_api_forumcomment` (`id`),
  CONSTRAINT `heritage_api_forumre_post_id_8f11184b_fk_heritage_` FOREIGN KEY (`post_id`) REFERENCES `heritage_api_forumpost` (`id`),
  CONSTRAINT `heritage_api_forumreport_handler_id_c1965bd9_fk_auth_user_id` FOREIGN KEY (`handler_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_forumreport_reporter_id_39ffaa79_fk_auth_user_id` FOREIGN KEY (`reporter_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| reason | varchar(20) | NO |  |  |
| description | longtext | NO |  |  |
| status | varchar(20) | NO |  |  |
| handler_note | longtext | NO |  |  |
| created_at | datetime(6) | NO |  |  |
| handled_at | datetime(6) | YES |  |  |
| comment_id | bigint | YES |  | 索引 |
| handler_id | int | YES |  | 索引 |
| post_id | bigint | YES |  | 索引 |
| reporter_id | int | NO |  | 索引 |

---

## heritage_api_forumtag

### 创建命令

`sql
CREATE TABLE `heritage_api_forumtag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` longtext NOT NULL,
  `color` varchar(7) NOT NULL,
  `post_count` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `heritage_api_forumtag_chk_1` CHECK ((`post_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| name | varchar(50) | NO |  | 唯一键 |
| description | longtext | NO |  |  |
| color | varchar(7) | NO |  |  |
| post_count | int unsigned | NO |  |  |
| created_at | datetime(6) | NO |  |  |

---

## heritage_api_forumuserfollow

### 创建命令

`sql
CREATE TABLE `heritage_api_forumuserfollow` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `follower_id` int NOT NULL,
  `following_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_forumuserfo_follower_id_following_id_f6e04597_uniq` (`follower_id`,`following_id`),
  KEY `heritage_api_forumus_following_id_ccdb4f11_fk_auth_user` (`following_id`),
  CONSTRAINT `heritage_api_forumus_follower_id_ddaf8b19_fk_auth_user` FOREIGN KEY (`follower_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_forumus_following_id_ccdb4f11_fk_auth_user` FOREIGN KEY (`following_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| follower_id | int | NO |  | 索引 |
| following_id | int | NO |  | 索引 |

---

## heritage_api_forumuserstats

### 创建命令

`sql
CREATE TABLE `heritage_api_forumuserstats` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `post_count` int unsigned NOT NULL,
  `comment_count` int unsigned NOT NULL,
  `like_received` int unsigned NOT NULL,
  `follower_count` int unsigned NOT NULL,
  `following_count` int unsigned NOT NULL,
  `level` int unsigned NOT NULL,
  `experience` int unsigned NOT NULL,
  `last_active_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `heritage_api_forumuserstats_user_id_2dfd260c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_forumuserstats_chk_1` CHECK ((`post_count` >= 0)),
  CONSTRAINT `heritage_api_forumuserstats_chk_2` CHECK ((`comment_count` >= 0)),
  CONSTRAINT `heritage_api_forumuserstats_chk_3` CHECK ((`like_received` >= 0)),
  CONSTRAINT `heritage_api_forumuserstats_chk_4` CHECK ((`follower_count` >= 0)),
  CONSTRAINT `heritage_api_forumuserstats_chk_5` CHECK ((`following_count` >= 0)),
  CONSTRAINT `heritage_api_forumuserstats_chk_6` CHECK ((`level` >= 0)),
  CONSTRAINT `heritage_api_forumuserstats_chk_7` CHECK ((`experience` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| post_count | int unsigned | NO |  |  |
| comment_count | int unsigned | NO |  |  |
| like_received | int unsigned | NO |  |  |
| follower_count | int unsigned | NO |  |  |
| following_count | int unsigned | NO |  |  |
| level | int unsigned | NO |  |  |
| experience | int unsigned | NO |  |  |
| last_active_at | datetime(6) | NO |  |  |
| user_id | int | NO |  | 唯一键 |

---

## heritage_api_heritage

### 创建命令

`sql
CREATE TABLE `heritage_api_heritage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `region` varchar(50) NOT NULL,
  `description` longtext NOT NULL,
  `history` longtext,
  `batch` varchar(50) DEFAULT NULL,
  `features` longtext,
  `gallery_image_urls` json NOT NULL DEFAULT (_utf8mb4'[]'),
  `inheritors` longtext,
  `main_image_url` varchar(500) DEFAULT NULL,
  `pinyin_name` varchar(200) DEFAULT NULL,
  `protection_measures` longtext,
  `related_works` longtext,
  `status` longtext,
  `value` longtext,
  `latitude` double DEFAULT NULL,
  `level` varchar(50) DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_heritage_name_de927af1_uniq` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| name | varchar(100) | NO |  | 唯一键 |
| category | varchar(50) | NO |  |  |
| region | varchar(50) | NO |  |  |
| description | longtext | NO |  |  |
| history | longtext | YES |  |  |
| batch | varchar(50) | YES |  |  |
| features | longtext | YES |  |  |
| gallery_image_urls | json | NO | _utf8mb4\'[]\' | DEFAULT_GENERATED |
| inheritors | longtext | YES |  |  |
| main_image_url | varchar(500) | YES |  |  |
| pinyin_name | varchar(200) | YES |  |  |
| protection_measures | longtext | YES |  |  |
| related_works | longtext | YES |  |  |
| status | longtext | YES |  |  |
| value | longtext | YES |  |  |
| latitude | double | YES |  |  |
| level | varchar(50) | YES |  |  |
| longitude | double | YES |  |  |

---

## heritage_api_heritageimage

### 创建命令

`sql
CREATE TABLE `heritage_api_heritageimage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `image` varchar(100) NOT NULL,
  `is_main` tinyint(1) NOT NULL,
  `heritage_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_api_heritageimage_heritage_id_01aca7b3_fk` (`heritage_id`),
  CONSTRAINT `heritage_api_heritageimage_heritage_id_01aca7b3_fk` FOREIGN KEY (`heritage_id`) REFERENCES `heritage_api_heritage` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| image | varchar(100) | NO |  |  |
| is_main | tinyint(1) | NO |  |  |
| heritage_id | bigint | NO |  | 索引 |

---

## heritage_api_news

### 创建命令

`sql
CREATE TABLE `heritage_api_news` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `summary` longtext,
  `content` longtext NOT NULL,
  `author` varchar(100) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  `source_url` varchar(500) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `publish_date` datetime(6) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `view_count` int unsigned NOT NULL,
  `tags` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `heritage_api_news_chk_1` CHECK ((`view_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| title | varchar(200) | NO |  |  |
| summary | longtext | YES |  |  |
| content | longtext | NO |  |  |
| author | varchar(100) | YES |  |  |
| source | varchar(200) | YES |  |  |
| source_url | varchar(500) | YES |  |  |
| image_url | varchar(500) | YES |  |  |
| publish_date | datetime(6) | NO |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| is_active | tinyint(1) | NO |  |  |
| view_count | int unsigned | NO |  |  |
| tags | varchar(200) | YES |  |  |

---

## heritage_api_policy

### 创建命令

`sql
CREATE TABLE `heritage_api_policy` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `summary` longtext,
  `content` longtext NOT NULL,
  `policy_number` varchar(100) DEFAULT NULL,
  `issuing_authority` varchar(100) NOT NULL,
  `policy_type` varchar(20) NOT NULL,
  `effective_date` date DEFAULT NULL,
  `publish_date` date NOT NULL,
  `source_url` varchar(500) DEFAULT NULL,
  `attachment_url` varchar(500) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `view_count` int unsigned NOT NULL,
  `tags` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `heritage_api_policy_chk_1` CHECK ((`view_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| title | varchar(200) | NO |  |  |
| summary | longtext | YES |  |  |
| content | longtext | NO |  |  |
| policy_number | varchar(100) | YES |  |  |
| issuing_authority | varchar(100) | NO |  |  |
| policy_type | varchar(20) | NO |  |  |
| effective_date | date | YES |  |  |
| publish_date | date | NO |  |  |
| source_url | varchar(500) | YES |  |  |
| attachment_url | varchar(500) | YES |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| is_active | tinyint(1) | NO |  |  |
| view_count | int unsigned | NO |  |  |
| tags | varchar(200) | YES |  |  |

---

## heritage_api_usercreation

### 创建命令

`sql
CREATE TABLE `heritage_api_usercreation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `type` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `media_file` varchar(100) DEFAULT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  `view_count` int unsigned NOT NULL,
  `like_count` int unsigned NOT NULL,
  `comment_count` int unsigned NOT NULL,
  `share_count` int unsigned NOT NULL,
  `tags` json NOT NULL,
  `is_featured` tinyint(1) NOT NULL,
  `is_public` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `published_at` datetime(6) DEFAULT NULL,
  `author_id` int NOT NULL,
  `heritage_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `heritage_ap_status_3be7e3_idx` (`status`,`is_public`,`created_at`),
  KEY `heritage_ap_author__eb7d21_idx` (`author_id`,`created_at`),
  KEY `heritage_ap_heritag_ecf11e_idx` (`heritage_id`,`created_at`),
  KEY `heritage_ap_type_846efa_idx` (`type`,`created_at`),
  CONSTRAINT `heritage_api_usercre_heritage_id_89212d28_fk_heritage_` FOREIGN KEY (`heritage_id`) REFERENCES `heritage_api_heritage` (`id`),
  CONSTRAINT `heritage_api_usercreation_author_id_2e28e55d_fk_auth_user_id` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `heritage_api_usercreation_chk_1` CHECK ((`view_count` >= 0)),
  CONSTRAINT `heritage_api_usercreation_chk_2` CHECK ((`like_count` >= 0)),
  CONSTRAINT `heritage_api_usercreation_chk_3` CHECK ((`comment_count` >= 0)),
  CONSTRAINT `heritage_api_usercreation_chk_4` CHECK ((`share_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| title | varchar(100) | NO |  |  |
| description | longtext | NO |  |  |
| type | varchar(20) | NO |  | 索引 |
| status | varchar(20) | NO |  | 索引 |
| media_file | varchar(100) | YES |  |  |
| thumbnail | varchar(100) | YES |  |  |
| view_count | int unsigned | NO |  |  |
| like_count | int unsigned | NO |  |  |
| comment_count | int unsigned | NO |  |  |
| share_count | int unsigned | NO |  |  |
| tags | json | NO |  |  |
| is_featured | tinyint(1) | NO |  |  |
| is_public | tinyint(1) | NO |  |  |
| created_at | datetime(6) | NO |  |  |
| updated_at | datetime(6) | NO |  |  |
| published_at | datetime(6) | YES |  |  |
| author_id | int | NO |  | 索引 |
| heritage_id | bigint | YES |  | 索引 |

---

## heritage_api_userfavorite

### 创建命令

`sql
CREATE TABLE `heritage_api_userfavorite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `heritage_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_userfavorite_user_id_heritage_id_d42ce744_uniq` (`user_id`,`heritage_id`),
  KEY `heritage_api_userfav_heritage_id_57908b9c_fk_heritage_` (`heritage_id`),
  CONSTRAINT `heritage_api_userfav_heritage_id_57908b9c_fk_heritage_` FOREIGN KEY (`heritage_id`) REFERENCES `heritage_api_heritage` (`id`),
  CONSTRAINT `heritage_api_userfavorite_user_id_f05fa963_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| created_at | datetime(6) | NO |  |  |
| heritage_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_userhistory

### 创建命令

`sql
CREATE TABLE `heritage_api_userhistory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `visit_time` datetime(6) NOT NULL,
  `heritage_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `heritage_api_userhistory_user_id_heritage_id_792f9ce4_uniq` (`user_id`,`heritage_id`),
  KEY `heritage_api_userhis_heritage_id_408d7300_fk_heritage_` (`heritage_id`),
  CONSTRAINT `heritage_api_userhis_heritage_id_408d7300_fk_heritage_` FOREIGN KEY (`heritage_id`) REFERENCES `heritage_api_heritage` (`id`),
  CONSTRAINT `heritage_api_userhistory_user_id_6e2ceba4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| visit_time | datetime(6) | NO |  |  |
| heritage_id | bigint | NO |  | 索引 |
| user_id | int | NO |  | 索引 |

---

## heritage_api_userprofile

### 创建命令

`sql
CREATE TABLE `heritage_api_userprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `avatar` varchar(100) DEFAULT NULL,
  `bio` longtext NOT NULL,
  `display_name` varchar(100) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `heritage_api_userprofile_user_id_5f35aad2_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
`

### 字段说明

| 字段名 | 类型 | 是否为空 | 默认值 | 备注 |
|--------|------|--------|--------|------|
| id | bigint | NO |  | 主键, auto_increment |
| avatar | varchar(100) | YES |  |  |
| bio | longtext | NO |  |  |
| display_name | varchar(100) | NO |  |  |
| user_id | int | NO |  | 唯一键 |

---

