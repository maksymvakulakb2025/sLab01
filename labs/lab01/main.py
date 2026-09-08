import os
import sys

sys.path.append(os.path.dirname(__file__))

from task1 import run_task1
from task2 import run_task2
from task3 import run_task3


def main():
    print("==========================================")
    print("   ЗАПУСК ЛАБОРАТОРНОЇ РОБОТИ №1 (ВАРІАНТ 5)")
    print("==========================================")
    run_task1()
    run_task2()
    run_task3()


if __name__ == "__main__":
    main()