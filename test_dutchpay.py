"""
테스트: 미리 구해 둔 정답과 프로그램의 결과가 같은지,
그리고 어떤 입력에서도 지켜져야 하는 성질이 지켜지는지 확인한다.
실행:  python test_dutchpay.py
"""

import os
import random
import tempfile

from dutchpay import (EXAMPLE_ITEMS, calculate_balances, check_items,
                      count_itemwise_transfers, make_message, make_transfers,
                      parse_amount, parse_people, read_items_from_csv)
from optimal import min_transfer_count

# 이 파일이 있는 폴더 (어느 폴더에서 실행해도 data 폴더를 찾을 수 있게 한다)
HERE = os.path.dirname(os.path.abspath(__file__))


def apply_transfers(balance, transfers):
    """송금을 실제로 적용했을 때 남는 잔액을 돌려준다. (모두 0이어야 정산 완료)"""
    remain = dict(balance)
    for sender, receiver, amount in transfers:
        remain[sender] += amount
        remain[receiver] -= amount
    return remain


def random_items(people_count):
    """무작위 결제 내역을 만든다. (금액은 100원 단위, 3천 원 ~ 20만 원)"""
    members = ["P" + str(i) for i in range(1, people_count + 1)]
    items = []
    for number in range(random.randint(3, 8)):
        amount = random.randint(30, 2000) * 100
        payer = random.choice(members)
        people = random.sample(members, random.randint(2, people_count))
        items.append(("항목" + str(number + 1), amount, payer, people))
    return items


# ---------------- 계획서 예시 (계획서에 적은 값과 비교) ----------------

def test_example_balances():
    paid, burden, balance = calculate_balances(EXAMPLE_ITEMS)
    assert paid == {"A": 160000, "B": 90000, "C": 24000, "D": 12000}
    assert burden == {"A": 79000, "B": 79000, "C": 49000, "D": 79000}
    assert balance == {"A": 81000, "B": 11000, "C": -25000, "D": -67000}


def test_example_transfers():
    paid, burden, balance = calculate_balances(EXAMPLE_ITEMS)
    transfers = make_transfers(balance)
    assert transfers == [("D", "A", 67000), ("C", "A", 14000), ("C", "B", 11000)]


def test_example_11_to_3():
    paid, burden, balance = calculate_balances(EXAMPLE_ITEMS)
    assert count_itemwise_transfers(EXAMPLE_ITEMS) == 11
    assert len(make_transfers(balance)) == 3
    assert min_transfer_count(balance) == 3      # 3회가 실제 최솟값


# ---------------- 나누어떨어지지 않는 금액 ----------------

def test_remainder_goes_to_payer():
    items = [("간식", 10000, "A", ["A", "B", "C"])]
    paid, burden, balance = calculate_balances(items)
    assert burden == {"A": 3334, "B": 3333, "C": 3333}   # 남는 1원은 결제자 A
    assert balance == {"A": 6666, "B": -3333, "C": -3333}
    assert sum(balance.values()) == 0


def test_payer_not_in_people():
    # A가 대신 결제만 하고 자신은 참여하지 않은 경우
    items = [("선물", 30000, "A", ["B", "C"])]
    paid, burden, balance = calculate_balances(items)
    assert balance == {"A": 30000, "B": -15000, "C": -15000}


# ---------------- 송금 결과의 성질 ----------------

def test_no_transfer_when_even():
    items = [("점심", 20000, "A", ["A", "B"]), ("저녁", 20000, "B", ["A", "B"])]
    paid, burden, balance = calculate_balances(items)
    assert make_transfers(balance) == []
    assert "주고받을 돈이 없습니다" in make_message(items, [])
    # 잔액의 합이 0이 아닌 잘못된 잔액은 계산하지 않고 오류를 낸다
    try:
        make_transfers({"A": 5000, "B": -3000})
        assert False, "오류가 나야 한다"
    except ValueError:
        pass


def test_random_cases():
    random.seed(1)
    for trial in range(1000):
        items = random_items(random.randint(2, 10))
        paid, burden, balance = calculate_balances(items)
        transfers = make_transfers(balance)
        assert sum(balance.values()) == 0                         # 검산
        remain = apply_transfers(balance, transfers)
        assert all(value == 0 for value in remain.values())       # 모두 정산됨
        assert all(amount > 0 for s, r, amount in transfers)      # 0원 송금 없음
        assert len(transfers) <= max(len(balance) - 1, 0)         # 최대 n-1번


# ---------------- 탐욕 알고리즘 vs 실제 최솟값 ----------------

def test_greedy_never_beats_optimal():
    random.seed(2)
    for trial in range(300):
        items = random_items(random.randint(2, 8))
        paid, burden, balance = calculate_balances(items)
        assert len(make_transfers(balance)) >= min_transfer_count(balance)


def test_greedy_can_miss_optimal():
    # 탐욕 알고리즘이 최솟값을 놓치는 예 (5명)
    balance = {"A": 5000, "B": 4000, "C": -4000, "D": -3000, "E": -2000}
    assert len(make_transfers(balance)) == 4
    assert min_transfer_count(balance) == 3      # B←C, A←D, A←E


# ---------------- 입력 처리 ----------------

def test_parse():
    assert parse_amount("160,000원") == 160000
    assert parse_amount(" 90000 ") == 90000
    assert parse_people("A B C") == ["A", "B", "C"]
    assert parse_people("A/B, C") == ["A", "B", "C"]
    for wrong in ["만원", "-5000", "", "12.5"]:
        try:
            parse_amount(wrong)
            assert False, "오류가 나야 하는 입력: " + wrong
        except ValueError:
            pass


def test_check_items():
    assert check_items(EXAMPLE_ITEMS) == []
    assert len(check_items([])) == 1
    assert len(check_items([("저녁", 0, "B", ["A", "B"])])) == 1        # 금액 0
    assert len(check_items([("카페", 5000, "", ["A", "B"])])) == 1      # 결제자 없음
    assert len(check_items([("택시", 5000, "A", [])])) == 1             # 참여자 없음
    assert len(check_items([("택시", 5000, "A", ["A", "A"])])) == 1     # 이름 중복


def write_temp_csv(text, encoding):
    """테스트용 임시 CSV 파일을 만들고 그 경로를 돌려준다."""
    handle, path = tempfile.mkstemp(suffix=".csv")
    os.close(handle)
    with open(path, "w", encoding=encoding, newline="") as f:
        f.write(text)
    return path


def test_csv():
    assert read_items_from_csv(os.path.join(HERE, "data", "trip.csv")) == EXAMPLE_ITEMS
    errors = check_items(read_items_from_csv(os.path.join(HERE, "data", "error_example.csv")))
    assert len(errors) == 3

    header = "항목,금액,결제자,참여자\n"
    expected = [("숙소", 160000, "민준", ["민준", "서연"])]

    # 엑셀의 기본 CSV 형식(CP949)으로 저장된 파일도 읽는다
    path = write_temp_csv(header + "숙소,160000,민준,민준 서연\n", "cp949")
    assert read_items_from_csv(path) == expected
    os.remove(path)

    # 첫 줄이 빈 줄이어도 제목 줄을 알아본다 / 따옴표로 감싼 "160,000원"도 읽는다
    path = write_temp_csv("\n" + header + '숙소,"160,000원",민준,민준 서연\n', "utf-8-sig")
    assert read_items_from_csv(path) == expected
    os.remove(path)

    # 따옴표 없이 160,000 이라고 쓰면 칸이 밀리므로 오류로 알려준다
    path = write_temp_csv(header + "숙소,160,000,민준,서연 지호\n", "utf-8")
    try:
        read_items_from_csv(path)
        assert False, "오류가 나야 한다"
    except ValueError as error:
        assert "2번째 줄" in str(error)
    os.remove(path)


# ---------------- 실행 ----------------

if __name__ == "__main__":
    tests = [
        test_example_balances, test_example_transfers, test_example_11_to_3,
        test_remainder_goes_to_payer, test_payer_not_in_people,
        test_no_transfer_when_even, test_random_cases,
        test_greedy_never_beats_optimal, test_greedy_can_miss_optimal,
        test_parse, test_check_items, test_csv,
    ]
    for test in tests:
        test()
        print("통과:", test.__name__)
    print()
    print("테스트 " + str(len(tests)) + "개 모두 통과")
