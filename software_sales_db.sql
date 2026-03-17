'''Criação bando de dados'''
CREATE DATABASE software_sales_db;

'''Criando senha de usurio'''
CREATE USER api_user WITH PASSWORD '577643121Aa.';

'''Conectando banco com usurio'''
GRANT ALL PRIVILEGES ON DATABASE software_sales_db TO api_user;