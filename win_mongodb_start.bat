@echo off
set _path=C:\Program Files\MongoDB\Server\3.2\bin
cd /d %_path%
title Mongo Server
mongod
pause