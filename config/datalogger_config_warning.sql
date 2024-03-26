-- MySQL dump 10.13  Distrib 8.0.34, for Win64 (x86_64)
--
-- Host: localhost    Database: wqms_onlimo
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

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
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `method` text NOT NULL,
  `h-hour` varchar(45) NOT NULL,
  `expression` text NOT NULL,
  `key` varchar(45) NOT NULL,
  `message` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `datalogger_config_warning`
--

LOCK TABLES `datalogger_config_warning` WRITE;
/*!40000 ALTER TABLE `datalogger_config_warning` DISABLE KEYS */;
INSERT INTO `datalogger_config_warning` VALUES (1,'send_klhk','3','uploaded_klhk = 3','check_transmission','f"Data sent KLHK = {data_sent}, it should be {count}"','Cek jumlah pengiriman ke KLHK hari ini'),(2,'send_klhk','3','uploaded_klhk != 3','check_waiting','f"{count} message(s) \'waiting/failed\' send to KLHK"','Cek jumlah pengiriman ke KLHK yang tidak berhasil hari ini'),(3,'send_klhk','3','','check_gen_refrence','f"Fatal error, the system did not generate reference today, please check Immediately"','Cek pembuatan generate refrence hari ini'),(4,'read_value','1','value < 7 and value >300','cod','Anomali COD ','Cek value COD'),(5,'read_value','1','f\"value != {cod*0.5} or value != {cod*0.25}\"','bod','Anomali BOD','Cek value BOD dari COD'),(6,'read_value','1','f\"value < {bod} and value > {cod}\"','toc','Anomali TOC','Cek value TOC dari COD dan BOD'),(7,'read_value','1','value < 10 and value > 60','tss','Anomali TSS','Cek value TSS'),(8,'read_value','1','f\"value < {tss}\"','turbidity','Anomali Turbidity','Cek value Turbidity'),(9,'read_value','1','value < 6 and value > 9','ph','Anomali PH','Cek value PH'),(10,'read_value','1','value < 1 and value > 1','amonia','Anomali amonia','Cek value amonia');
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

-- Dump completed on 2024-03-23  4:30:22
