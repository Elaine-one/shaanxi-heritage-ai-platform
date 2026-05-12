from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("heritage_api", "0018_add_admin_operation_log"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                'DROP TABLE IF EXISTS `heritage_api_travelplanitem`;',
                'DROP TABLE IF EXISTS `heritage_api_travelplanedithistory`;',
                'DROP TABLE IF EXISTS `heritage_api_travelplansession`;',
                'DROP TABLE IF EXISTS `heritage_api_travelplanday`;',
                'DROP TABLE IF EXISTS `heritage_api_travelplan`;',
            ],
            reverse_sql=[
                'CREATE TABLE `heritage_api_travelplan` (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY);',
                'CREATE TABLE `heritage_api_travelplanday` (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY);',
                'CREATE TABLE `heritage_api_travelplansession` (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY);',
                'CREATE TABLE `heritage_api_travelplanedithistory` (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY);',
                'CREATE TABLE `heritage_api_travelplanitem` (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY);',
            ],
        ),
    ]
