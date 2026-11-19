"""
더치페이 최소 송금 계산기
==========================
여러 명이 함께 쓴 돈을 정산할 때,
"누가 누구에게 얼마를 보내면 되는지"를 적은 송금 횟수로 알려주는 프로그램.

실행 방법
    python dutchpay.py                 -> 메뉴가 나온다 (예시 / CSV / 직접 입력)
    python dutchpay.py data/trip.csv   -> CSV 파일을 바로 계산한다

결제 내역 1건은 튜플 하나로 표현한다.
    (항목 이름, 금액, 결제자, [참여자 목록])
    예) ("저녁", 90000, "B", ["A", "B", "D"])
"""

import csv
import sys
import unicodedata


# 계획서에서 사용한 예시: 4명(A~D)이 1박 2일 여행을 다녀온 상황
EXAMPLE_ITEMS = [
    ("숙소", 160000, "A", ["A", "B", "C", "D"]),
    ("저녁", 90000, "B", ["A", "B", "D"]),      # C는 저녁 불참
    ("카페", 24000, "C", ["A", "B", "C", "D"]),
    ("택시", 12000, "D", ["A", "B", "C", "D"]),
]


# ------------------------------------------------------------
# 1. 입력: 글자를 숫자와 목록으로 바꾸기
# ------------------------------------------------------------

def parse_amount(text):
    """'160,000원' 같은 글자를 정수 160000으로 바꾼다. 숫자가 아니면 오류를 낸다."""
    cleaned = text.replace(",", "").replace("원", "").replace(" ", "")
    if not cleaned.isdecimal():      # 0~9 숫자로만 이루어져 있는지 확인
        raise ValueError("금액 '" + text + "'은(는) 0 이상의 정수가 아닙니다.")
    return int(cleaned)


def parse_people(text):
    """'A B C', 'A/B/C', 'A,B,C' 를 모두 ['A', 'B', 'C'] 로 바꾼다."""
    for mark in ["/", ",", ";"]:
        text = text.replace(mark, " ")
    return text.split()


def read_items_from_csv(path):
    """CSV 파일에서 결제 내역을 읽는다. 칸 순서: 항목, 금액, 결제자, 참여자"""
    items = []
    line_no = 0
    first_row = True
    for row in csv.reader(read_lines(path)):
        line_no += 1
        # 빈 줄은 건너뛴다
        if len(row) == 0 or "".join(row).strip() == "":
            continue
        if len(row) < 4:
            raise ValueError(str(line_no) + "번째 줄: 칸이 4개(항목, 금액, 결제자, 참여자) 필요합니다.")
        # 내용이 있는 첫 줄의 금액 칸에 숫자가 하나도 없으면 제목 줄로 보고 건너뛴다
        if first_row:
            first_row = False
            if not any(ch.isdecimal() for ch in row[1]):
                continue
        # '160,000'처럼 금액에 쉼표를 쓰면 칸이 둘로 나뉘어 결제자 칸에 숫자가 들어온다
        if row[2].replace("원", "").strip().isdecimal():
            raise ValueError(str(line_no) + "번째 줄: 금액에 쉼표가 들어 있습니다. 160000처럼 쉼표 없이 적어 주세요.")
        try:
            amount = parse_amount(row[1])
        except ValueError as error:
            raise ValueError(str(line_no) + "번째 줄: " + str(error))
        name = row[0].strip()
        payer = row[2].strip()
        # 참여자를 쉼표로 구분해 적으면 칸이 여러 개로 나뉘므로 다시 합친다
        people = parse_people(" ".join(row[3:]))
        items.append((name, amount, payer, people))
    return items


def read_lines(path):
    """
    파일을 줄 목록으로 읽는다.
    먼저 UTF-8로 읽고, 읽히지 않으면 엑셀의 기본 CSV 형식(CP949)으로 다시 읽는다.
    utf-8-sig: 엑셀에서 'CSV UTF-8'로 저장하면 맨 앞에 붙는 표시(BOM)를 떼어 준다.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return f.read().splitlines()
    except UnicodeDecodeError:
        with open(path, newline="", encoding="cp949") as f:
            return f.read().splitlines()


def input_items():
    """키보드로 결제 내역을 하나씩 입력받는다."""
    print()
    members = []
    while len(members) < 2:
        members = parse_people(input("정산할 사람들의 이름 (띄어쓰기로 구분): "))
        if len(members) < 2:
            print("  -> 2명 이상 입력해 주세요.")
        elif len(members) != len(set(members)):
            print("  -> 같은 이름이 두 번 들어 있습니다.")
            members = []

    items = []
    while True:
        print()
        name = input(str(len(items) + 1) + "번째 항목 이름 (끝내려면 그냥 Enter): ").strip()
        if name == "":
            break

        # 금액: 올바른 숫자가 들어올 때까지 다시 묻는다
        while True:
            try:
                amount = parse_amount(input("  금액: "))
                if amount > 0:
                    break
                print("  -> 금액은 0보다 커야 합니다.")
            except ValueError as error:
                print("  ->", error)

        # 결제자: 처음에 입력한 사람 중 한 명이어야 한다
        while True:
            payer = input("  결제자: ").strip()
            if payer in members:
                break
            print("  -> " + ", ".join(members) + " 중에서 입력해 주세요.")

        # 참여자: 그냥 Enter를 누르면 전원 참여
        while True:
            people = parse_people(input("  참여자 (전원이면 그냥 Enter): "))
            if len(people) == 0:
                people = list(members)
            wrong = [p for p in people if p not in members]
            if len(wrong) > 0:
                print("  -> 처음에 입력하지 않은 이름:", ", ".join(wrong))
            elif len(people) != len(set(people)):
                print("  -> 같은 이름이 두 번 들어 있습니다.")
            else:
                break

        items.append((name, amount, payer, people))
    return items


def check_items(items):
    """입력 실수를 찾아 오류 메시지 목록으로 돌려준다. 문제가 없으면 빈 목록."""
    errors = []
    if len(items) == 0:
        errors.append("결제 내역이 하나도 없습니다.")
    for name, amount, payer, people in items:
        label = "[" + name + "] "
        if name == "":
            errors.append("항목 이름이 비어 있는 줄이 있습니다.")
        if amount <= 0:
            errors.append(label + "금액은 0보다 커야 합니다.")
        if payer == "":
            errors.append(label + "결제자가 비어 있습니다.")
        if len(people) == 0:
            errors.append(label + "참여자가 한 명도 없습니다.")
        if len(people) != len(set(people)):
            errors.append(label + "참여자에 같은 이름이 두 번 들어 있습니다.")
    return errors


# ------------------------------------------------------------
# 2. 계산 1단계: 사람별 낸 돈, 부담액, 잔액
# ------------------------------------------------------------

def calculate_balances(items):
    """
    사람별로 세 가지 값을 계산해 딕셔너리 3개로 돌려준다.
        paid[사람]    = 실제로 낸 돈
        burden[사람]  = 부담해야 할 돈 (항목 금액 ÷ 참여 인원의 합)
        balance[사람] = 낸 돈 - 부담액   (+면 받을 사람, -면 보낼 사람)

    나누어떨어지지 않는 금액은 원 단위까지만 나누고,
    남는 몇 원은 그 항목의 결제자가 부담한다.
    """
    paid = {}
    burden = {}

    for name, amount, payer, people in items:
        # 처음 나온 사람은 0원으로 등록한다
        for person in [payer] + people:
            if person not in paid:
                paid[person] = 0
                burden[person] = 0

        paid[payer] += amount

        share = amount // len(people)          # 1인당 부담액 (원 단위 미만 버림)
        rest = amount - share * len(people)    # 나누고 남은 돈 (0원 ~ 인원수-1원)
        for person in people:
            burden[person] += share
        burden[payer] += rest                  # 남는 돈은 결제자가 부담

    balance = {}
    for person in paid:
        balance[person] = paid[person] - burden[person]

    # 자동 검산: 받을 돈의 합과 보낼 돈의 합은 같아야 하므로 잔액의 합은 항상 0
    if sum(balance.values()) != 0:
        raise RuntimeError("검산 실패: 잔액의 합이 0이 아닙니다.")

    return paid, burden, balance


# ------------------------------------------------------------
# 3. 계산 2단계: 송금 매칭 (탐욕 알고리즘)
# ------------------------------------------------------------

def make_transfers(balance):
    """
    잔액이 가장 큰 사람(받을 돈 최대)과 가장 작은 사람(보낼 돈 최대)을
    짝지어 송금시키는 일을, 모든 잔액이 0이 될 때까지 반복한다.
    결과: [(보내는 사람, 받는 사람, 금액), ...]
    """
    # 잔액의 합이 0이 아니면 아무리 송금해도 끝나지 않으므로 미리 막는다
    if sum(balance.values()) != 0:
        raise ValueError("잔액의 합이 0이 아니어서 송금을 계산할 수 없습니다.")

    remain = dict(balance)      # 원본을 바꾸지 않도록 복사해서 사용
    transfers = []

    while len(remain) > 0:
        receiver = max(remain, key=remain.get)   # 잔액이 가장 큰 사람
        sender = min(remain, key=remain.get)     # 잔액이 가장 작은 사람

        if remain[receiver] == 0:                # 가장 큰 잔액이 0이면 모두 정산 끝
            break

        amount = min(remain[receiver], -remain[sender])
        transfers.append((sender, receiver, amount))
        remain[receiver] -= amount
        remain[sender] += amount                 # 둘 중 최소 한 명은 잔액이 0이 된다
        # (마지막 송금에서는 두 명이 함께 0이 되므로, n명이면 많아야 n-1번 반복한다)

    return transfers


def find_similar_names(names):
    """대소문자만 다른 이름(A와 a)을 짝지어 돌려준다. 입력 실수일 가능성이 높다."""
    seen = {}
    pairs = []
    for person in names:
        key = person.lower()
        if key in seen:
            pairs.append((seen[key], person))
        else:
            seen[key] = person
    return pairs


def count_itemwise_transfers(items):
    """비교용: 항목마다 따로 결제자에게 송금할 때의 송금 횟수."""
    count = 0
    for name, amount, payer, people in items:
        for person in people:
            if person != payer:
                count += 1
    return count


# ------------------------------------------------------------
# 4. 출력
# ------------------------------------------------------------

def won(amount):
    """160000 -> '160,000원'"""
    return format(amount, ",") + "원"


def pad(text, width):
    """한글은 화면에서 두 칸을 차지하므로, 그만큼 계산해서 오른쪽에 빈칸을 채운다."""
    used = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            used += 2
        else:
            used += 1
    return text + " " * max(width - used, 0)


def make_message(items, transfers):
    """단톡방에 그대로 붙여넣을 수 있는 송금 안내 메시지를 만든다."""
    total = 0
    for name, amount, payer, people in items:
        total += amount

    lines = []
    lines.append("[정산 안내]")
    lines.append("총 지출 " + won(total) + " (" + str(len(items)) + "개 항목)")
    if len(transfers) == 0:
        lines.append("주고받을 돈이 없습니다. 정산 끝!")
    else:
        lines.append("아래 " + str(len(transfers)) + "건만 송금하면 정산이 끝납니다.")
        for sender, receiver, amount in transfers:
            lines.append("- " + sender + " → " + receiver + " : " + won(amount))
    return "\n".join(lines)


def print_report(items):
    """결제 내역을 받아 계산하고, 결과를 화면에 출력한다."""
    errors = check_items(items)
    if len(errors) > 0:
        print()
        print("입력 오류가 있어 계산하지 않았습니다.")
        for message in errors:
            print("  -", message)
        return

    paid, burden, balance = calculate_balances(items)
    transfers = make_transfers(balance)

    print()
    print("■ 결제 내역")
    for name, amount, payer, people in items:
        print("  " + pad(name, 12) + " " + won(amount).rjust(10) + "   결제 " + pad(payer, 8)
              + " 참여 " + ", ".join(people))

    print()
    print("■ 사람별 잔액  (잔액 = 낸 돈 - 부담액)")
    print("  " + pad("사람", 8) + "낸 돈".rjust(9) + "부담액".rjust(9) + "잔액".rjust(10))
    for person in balance:
        if balance[person] > 0:
            note = "받을 사람"
        elif balance[person] < 0:
            note = "보낼 사람"
        else:
            note = "정산 없음"
        print("  " + pad(person, 8) + format(paid[person], ",").rjust(11)
              + format(burden[person], ",").rjust(12)
              + (format(balance[person], "+,") if balance[person] != 0 else "0").rjust(12)
              + "   " + note)
    print("  검산: 잔액의 합 =", sum(balance.values()))
    for first, second in find_similar_names(balance):
        print("  주의: '" + first + "'와(과) '" + second + "'는 서로 다른 사람으로 계산했습니다. "
              + "같은 사람이면 이름을 똑같이 적어 주세요.")

    print()
    print("■ 송금 방법")
    number = 0
    for sender, receiver, amount in transfers:
        number += 1
        print("  " + str(number) + ". " + sender + " → " + receiver + "   " + won(amount))
    print("  항목마다 따로 보낼 때 " + str(count_itemwise_transfers(items)) + "회  →  "
          + "이 프로그램 " + str(len(transfers)) + "회")

    print()
    print("■ 단톡방 안내 메시지")
    print(make_message(items, transfers))


# ------------------------------------------------------------
# 5. 프로그램 시작점
# ------------------------------------------------------------

def main():
    print("=" * 46)
    print("  더치페이 최소 송금 계산기")
    print("=" * 46)

    # 실행할 때 파일 이름을 함께 주면 그 파일을 바로 계산한다
    if len(sys.argv) > 1:
        try:
            items = read_items_from_csv(sys.argv[1])
        except FileNotFoundError:
            print("파일을 찾을 수 없습니다:", sys.argv[1])
            return
        except (OSError, ValueError) as error:
            print("파일을 읽지 못했습니다:", error)
            return
        print_report(items)
        return

    print("1. 예시 데이터로 계산 (4명 여행)")
    print("2. CSV 파일 불러오기")
    print("3. 직접 입력하기")
    choice = input("번호를 선택하세요: ").strip()

    if choice == "1":
        items = EXAMPLE_ITEMS
    elif choice == "2":
        # 파일을 끌어다 놓으면 경로 앞뒤에 따옴표가 붙을 수 있어 떼어 낸다
        path = input("CSV 파일 경로: ").strip().strip('"').strip("'")
        try:
            items = read_items_from_csv(path)
        except FileNotFoundError:
            print("파일을 찾을 수 없습니다:", path)
            return
        except (OSError, ValueError) as error:
            print("파일을 읽지 못했습니다:", error)
            return
    elif choice == "3":
        items = input_items()
    else:
        print("1, 2, 3 중에서 선택해 주세요.")
        return

    print_report(items)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        # 입력 도중에 Ctrl+C 등을 눌러 중단한 경우
        print()
        print("입력이 중단되어 프로그램을 끝냅니다.")
