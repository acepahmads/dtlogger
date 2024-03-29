-- MySQL dump 10.13  Distrib 8.0.36, for Linux (x86_64)
--
-- Host: localhost    Database: aqms
-- ------------------------------------------------------
-- Server version	8.0.36-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `datalogger_config_warning`
--

DROP TABLE IF EXISTS `datalogger_config_warning`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `datalogger_config_warning` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `method` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `h-hour` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `expression` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `key` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `message` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `min` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `max` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `datalogger_config_warning`
--

LOCK TABLES `datalogger_config_warning` WRITE;
/*!40000 ALTER TABLE `datalogger_config_warning` DISABLE KEYS */;
INSERT INTO `datalogger_config_warning` VALUES (1,'send_klhk','3','uploaded_klhk = 3','check_transmission','f\"Data sent KLHK = {data_sent}, it should be {count}\"',NULL,NULL,'Cek jumlah pengiriman ke KLHK hari ini'),(2,'send_klhk','3','uploaded_klhk != 3','check_waiting','f\"{count} message(s) \'waiting/failed\' send to KLHK\"',NULL,NULL,'Cek jumlah pengiriman ke KLHK yang tidak berhasil hari ini'),(3,'send_klhk','3','','check_gen_refrence','f\"Fatal error, the system did not generate reference today, please check Immediately\"',NULL,NULL,'Cek pembuatan generate refrence hari ini'),(16,'read_value','1','pm2_5 > pm10','pm2.5','f\"PM2.5 {value} Anomali ({expression})\"',NULL,NULL,NULL),(17,'read_value','1','value < 25 or value > 35','temperature','f\"Temperature {value} Anomali ({expression})\"',NULL,NULL,NULL),(18,'read_value','1','value > 350','pm10','f\"PM10 {value} Anomali ({expression})\"',NULL,NULL,NULL),(19,'read_value','1','value > 150.4','pm2.5','f\"PM2.5 {value} Anomali ({expression})\"',NULL,NULL,NULL),(20,'read_value','1','value > 400','so2','f\"SO2 {value} Anomali ({expression})\"',NULL,NULL,NULL),(21,'read_value','1','value > 15000','co','f\"CO {value} Anomali ({expression})\"',NULL,NULL,NULL),(22,'read_value','1','value > 400','o3','f\"O3 {value} Anomali ({expression})\"',NULL,NULL,NULL),(23,'read_value','1','value > 1130','no2','f\"NO2 {value} Anomali ({expression})\"',NULL,NULL,NULL),(24,'read_value','1','value > 215','hc','f\"HC {value} Anomali ({expression})\"',NULL,NULL,NULL),(25,'stuck_value','1','count > 5','pm2.5','PM2.5 Stuck',NULL,NULL,NULL),(26,'stuck_value','1','count > 5','pm10','PM10 Stuck',NULL,NULL,NULL),(27,'stuck_value','1','count > 5','so2','SO2 Stuck',NULL,NULL,NULL),(28,'stuck_value','1','count > 5','co','CO Stuck',NULL,NULL,NULL),(29,'stuck_value','1','count > 5','o3','O3 Stuck',NULL,NULL,NULL),(30,'stuck_value','1','count > 5','no2','NO2 Stuck',NULL,NULL,NULL),(31,'stuck_value','1','count > 5','hc','HC Stuck',NULL,NULL,NULL),(32,'stuck_value','1','count > 5','temperature','Temperature Stuck',NULL,NULL,NULL);
/*!40000 ALTER TABLE `datalogger_config_warning` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-03-29 17:38:08
