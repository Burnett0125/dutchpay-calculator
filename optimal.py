"""
검증용: 실제 최소 송금 횟수 구하기 (완전 탐색)
================================================
dutchpay.py 의 탐욕 알고리즘은 빠르지만 항상 최솟값을 보장하지는 않는다.
그래서 가능한 경우를 모두 해 보는 방법으로 실제 최솟값을 구해
탐욕 알고리즘의 결과와 비교한다.

아이디어
    잔액이 0이 아닌 첫 번째 사람을 고른다.
    이 사람의 잔액 전부를 '부호가 반대인 다른 사람' 한 명에게 넘긴다. (송금 1회)
    그러면 첫 번째 사람은 정산이 끝나고, 남은 사람들로 같은 일을 반복한다.
    누구에게 넘길지를 전부 시도해서 그중 가장 적은 횟수를 답으로 한다.

경우의 수가 인원에 따라 급격히 늘어나므로 10명 안팎까지만 쓴다.
"""


def min_transfer_count(balance):
    """잔액 딕셔너리를 받아 가능한 최소 송금 횟수를 돌려준다."""
    debts = [value for value in balance.values() if value != 0]
    if len(debts) == 0:
        return 0

    # n명이면 n-1번으로는 항상 정산할 수 있으므로 여기서 시작해 더 줄일 수 있는지 찾는다
    best = len(debts) - 1

    def search(start, count):
        nonlocal best

        # 이미 정산이 끝난 사람(잔액 0)은 건너뛴다
        while start < len(debts) and debts[start] == 0:
            start += 1

        if start == len(debts):          # 모두 정산됨
            if count < best:
                best = count
            return

        if count + 1 >= best:            # 더 해 봐도 지금까지의 최고 기록보다 못함
            return

        tried = set()                    # 같은 금액인 상대는 한 번만 시도
        for i in range(start + 1, len(debts)):
            if debts[i] * debts[start] < 0 and debts[i] not in tried:
                tried.add(debts[i])
                debts[i] += debts[start]         # start의 잔액을 i에게 모두 넘긴다
                search(start + 1, count + 1)
                debts[i] -= debts[start]         # 원래대로 되돌리고 다음 상대를 시도

    search(0, 0)
    return best
