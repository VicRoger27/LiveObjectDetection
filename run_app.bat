@echo off
title Live Object Detection & Auto-Labeling Suite
cd /d "%~dp0"
start "" python anylabeling/app.py %*
exit
