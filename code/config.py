# 配置

import json
import os
import asyncio
import threading
import time
import schedule
import datetime
from typing import Callable
from code.models import BotConfig
from code.database import MySQLConnecter
from code.agent import MemoryChatRobot

class ScheduleTask:
    def __init__(self, name="Unknown"):
        self.name = name
        self.tasks = []
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=True, name=f"SchedulerLoop-{name}")
        self.loop_thread.start()
        self.schedule_instance = schedule.Scheduler()
        self.schedule_thread = threading.Thread(target=self._run_pending, daemon=True, name=f"SchedulerPending-{name}")
        self.schedule_thread.start()
        self.task_counter = 0

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _run_pending(self):
        while self.running:
            self.schedule_instance.run_pending()
            time.sleep(0.1)

    def _run_async_task(self, task: Callable, *args, **kwargs):
        if asyncio.iscoroutinefunction(task):
            asyncio.run_coroutine_threadsafe(task(*args, **kwargs), self.loop)
        else:
            task(*args, **kwargs)

    def schedule_task(self, delay: int, task: Callable, *args, **kwargs):
        self.task_counter += 1
        job_id = f"single_{self.task_counter}"
        def execute_once():
            self._run_async_task(task, *args, **kwargs)
            self.tasks = [t for t in self.tasks if t["id"] != job_id]
        timer = threading.Timer(delay, execute_once)
        timer.daemon = True
        timer.start()
        class MockJob:
            def __init__(self, job_id):
                self.id = job_id
                self.next_run = datetime.datetime.now() + datetime.timedelta(seconds=delay)
        mock_job = MockJob(job_id)
        self.tasks.append({"id": job_id, "job": mock_job, "timer": timer})
        return job_id

    def schedule_loop_task(self, interval: int, task: Callable, *args, **kwargs):
        self.task_counter += 1
        job_id = f"loop_{self.task_counter}"
        job = self.schedule_instance.every(interval).seconds.do(self._run_async_task, task, *args, **kwargs)
        self.tasks.append({"id": job_id, "job": job})
        return job_id

    def cancel_all_tasks(self):
        for task in self.tasks:
            if "timer" in task:
                task["timer"].cancel()
        self.schedule_instance.clear()
        self.tasks.clear()

class ConfigManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.work_path = os.getcwd()
        self.config_path = self.work_path.replace("\\", "/") + "/config.json"
        with open(self.config_path, 'r', encoding='UTF-8') as f:
            config_data = json.load(f)
        self.bot_config = BotConfig.load(config_data)
        self.mysql_connector = MySQLConnecter(self.bot_config)
        self.chat_robot = MemoryChatRobot(self.bot_config, self.mysql_connector)
        self.scheduler = ScheduleTask("bot-scheduler")

config_manager = ConfigManager()

