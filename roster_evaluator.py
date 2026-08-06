from team import Team


class RosterEvaluator:

    def evaluate(self, team: Team):

        score = 0

        qb = team.count_position("QB")
        rb = team.count_position("RB")
        wr = team.count_position("WR")
        te = team.count_position("TE")
        dst = team.count_position("DST")
        k = team.count_position("K")

        # QB
        if qb == 1:
            score += 10
        elif qb == 2:
            score += 8
        else:
            score += 4

        # RB
        score += min(rb, 5) * 6

        # WR
        score += min(wr, 5) * 6

        # TE
        if te == 1:
            score += 10
        elif te == 2:
            score += 8
        else:
            score += 4

        # DST
        if dst == 1:
            score += 5

        # K
        if k == 1:
            score += 5

        return {
            "overall": score,
            "QB": qb,
            "RB": rb,
            "WR": wr,
            "TE": te,
            "DST": dst,
            "K": k,
        }