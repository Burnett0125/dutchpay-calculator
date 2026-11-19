"""
실험: 탐욕 알고리즘은 실제 최솟값과 얼마나 가까운가?
실행:  python experiment.py     (몇 초 걸림)

실험 A  실제 정산처럼 금액이 다양한 무작위 결제 내역 (100원 단위)
실험 B  잔액이 1,000원 단위로 딱 떨어지는 경우 (탐욕 알고리즘에 불리한 상황)

난수 씨앗(seed)을 고정했으므로 몇 번을 실행해도 같은 결과가 나온다.
"""

import random
import time

from dutchpay import calculate_balances, count_itemwise_transfers, make_transfers
from optimal import min_transfer_count

TRIALS = 1000      # 인원수마다 반복할 횟수


def random_items(people_count):
    """무작위 결제 내역: 항목 3~8개, 금액 3천 원 ~ 20만 원 (100원 단위)"""
    members = ["P" + str(i) for i in range(1, people_count + 1)]
    items = []
    for number in range(random.randint(3, 8)):
        amount = random.randint(30, 2000) * 100
        payer = random.choice(members)
        people = random.sample(members, random.randint(2, people_count))
        items.append(("항목" + str(number + 1), amount, payer, people))
    return items


def random_round_balance(people_count):
    """1,000원 단위로 떨어지는 무작위 잔액 (-9,000원 ~ +9,000원, 합은 0)"""
    while True:
        values = [random.randint(-9, 9) * 1000 for i in range(people_count - 1)]
        last = -sum(values)
        if abs(last) <= 9000:
            values.append(last)
            balance = {}
            for i in range(people_count):
                balance["P" + str(i + 1)] = values[i]
            return balance


def experiment_a():
    print("실험 A: 금액이 다양한 무작위 결제 내역 (인원수마다 " + str(TRIALS) + "건)")
    print("  인원   항목별 송금   탐욕 송금   최소 송금   탐욕=최소인 비율")
    total_same = 0
    total_cases = 0
    for people_count in range(3, 11):
        sum_itemwise = 0
        sum_greedy = 0
        sum_best = 0
        same = 0
        for trial in range(TRIALS):
            items = random_items(people_count)
            paid, burden, balance = calculate_balances(items)
            greedy = len(make_transfers(balance))
            best = min_transfer_count(balance)
            sum_itemwise += count_itemwise_transfers(items)
            sum_greedy += greedy
            sum_best += best
            if greedy == best:
                same += 1
        total_same += same
        total_cases += TRIALS
        print("  " + str(people_count).rjust(3) + "명"
              + format(sum_itemwise / TRIALS, ".2f").rjust(12) + "회"
              + format(sum_greedy / TRIALS, ".2f").rjust(10) + "회"
              + format(sum_best / TRIALS, ".2f").rjust(10) + "회"
              + format(same / TRIALS * 100, ".1f").rjust(15) + "%")
    print("  전체 " + str(total_cases) + "건 중 " + str(total_same) + "건에서 탐욕 = 최소")


def experiment_b():
    print("실험 B: 잔액이 1,000원 단위로 떨어지는 경우 (인원수마다 " + str(TRIALS) + "건)")
    print("  인원   탐욕 송금   최소 송금   탐욕=최소인 비율   최대 차이")
    for people_count in range(3, 11):
        sum_greedy = 0
        sum_best = 0
        same = 0
        max_gap = 0
        for trial in range(TRIALS):
            balance = random_round_balance(people_count)
            greedy = len(make_transfers(balance))
            best = min_transfer_count(balance)
            sum_greedy += greedy
            sum_best += best
            if greedy == best:
                same += 1
            if greedy - best > max_gap:
                max_gap = greedy - best
        print("  " + str(people_count).rjust(3) + "명"
              + format(sum_greedy / TRIALS, ".2f").rjust(10) + "회"
              + format(sum_best / TRIALS, ".2f").rjust(10) + "회"
              + format(same / TRIALS * 100, ".1f").rjust(15) + "%"
              + str(max_gap).rjust(10) + "회")


def show_counter_example():
    print("탐욕 알고리즘이 최솟값을 놓치는 예 (5명)")
    balance = {"A": 5000, "B": 4000, "C": -4000, "D": -3000, "E": -2000}
    print("  잔액:", balance)
    for sender, receiver, amount in make_transfers(balance):
        print("  탐욕: " + sender + " → " + receiver + "  " + format(amount, ",") + "원")
    print("  탐욕 " + str(len(make_transfers(balance))) + "회, 실제 최소 "
          + str(min_transfer_count(balance)) + "회 (C→B 4,000 / D→A 3,000 / E→A 2,000)")


if __name__ == "__main__":
    random.seed(2026)
    start = time.time()
    experiment_a()
    print()
    experiment_b()
    print()
    show_counter_example()
    print()
    print("걸린 시간: " + format(time.time() - start, ".1f") + "초")
