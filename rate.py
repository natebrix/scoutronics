# rate.py

from trueskill import *
from collections import defaultdict

# r3 = Rating()  # 3P's skill
# (new_r1,), (new_r2, new_r3) = rate([t1, t2], ranks=[0, 1])

# class trueskill.TrueSkill(mu=25.0, sigma=8.333333333333334, beta=4.166666666666667, tau=0.08333333333333334, draw_probability=0.1, backend=None)
# env.make_as_global() 
# env.create_rating()

def score_data_frame(r):
    sc = pd.DataFrame(r.items(), columns=['t', 's'])
    sc['score'] = sc['s'].apply(lambda s: s.mu)
    return sc.sort_values(by='score')


#frc
def score_event_frc_old(em):
    env = TrueSkill(draw_probability = 0)
    env.make_as_global()
    r = defaultdict(Rating)
    for m in em['Matches']:
        red = [t['teamNumber'] for t in m['teams'] if t['station'][0] == 'R']
        blue = [t['teamNumber'] for t in m['teams'] if t['station'][0] != 'R']
        if m['scoreRedFinal'] is not None:
            red_wins = m['scoreRedFinal'] > m['scoreBlueFinal']
            score = 1 if red_wins else 0
            rr = [r[t] for t in red]
            rb = [r[t] for t in blue]
            new_red, new_blue = rate([rr, rb], ranks=[score, 1-score])
            for i, t in enumerate(red):
                r[t] = new_red[i]
            for i, t in enumerate(blue):
                r[t] = new_blue[i]
    return score_data_frame(r)


def score_event_frc(df):
    em = df_em.sort_values(by='actual_time')
    env = TrueSkill(draw_probability = 0)
    env.make_as_global()
    r = defaultdict(Rating)
    for i in range(em.shape[0]):
        m = em.loc[i, :]
        if m['red_score'] is not None:
            red_wins = (m['winning_alliance'] == 'red')
            score = 1 if red_wins else 0
            rr = [r[t] for t in m['red_teams']]
            rb = [r[t] for t in m['blue_teams']]
            new_red, new_blue = rate([rr, rb], ranks=[score, 1-score])
            for i, t in enumerate(m['red_teams']):
                r[t] = new_red[i]
            for i, t in enumerate(m['blue_teams']):
                r[t] = new_blue[i]
    return score_data_frame(r)

def event_match_row(m):
    return [m['event_key'], m['key'], m['match_number'], m['actual_time'], m['winning_alliance'], m['alliances']['red']['team_keys'], m['alliances']['red']['score'], m['score_breakdown']['red']['autoPoints'], m['score_breakdown']['red']['teleopPoints'], m['alliances']['blue']['team_keys'], m['alliances']['blue']['score'], m['score_breakdown']['blue']['autoPoints'], m['score_breakdown']['blue']['teleopPoints']]

def event_match_data(em):
    rs = [event_match_row(m) for m in em]
    df = pd.DataFrame(rs, columns=['event_key', 'key', 'match_number', 'actual_time', 'winning_alliance', 'red_teams', 'red_score', 'blue_teams', 'blue_score'])
    df.sort_values(by='actual_time', inplace=True)
    return df

# todo: take a data frame
# todo: order the df by match time or number
def score_event_tba(em):
    env = TrueSkill(draw_probability = 0)
    env.make_as_global()
    r = defaultdict(Rating)
    for m in em:
        red = m['alliances']['red']['team_keys']
        blue = m['alliances']['blue']['team_keys']
        if m['winning_alliance'] is not None:
            # todo base it on a column or pass in a delegate
            score = 1 if (m['winning_alliance'] == 'red') else 0
            rr = [r[t] for t in red]
            rb = [r[t] for t in blue]
            new_red, new_blue = rate([rr, rb], ranks=[score, 1-score])
            for i, t in enumerate(red):
                r[t] = new_red[i]
            for i, t in enumerate(blue):
                r[t] = new_blue[i]
    return score_data_frame(r)
