import requests

branch_master = requests.get('https://api.github.com/repos/interlegis/sapl/commits?per_page=100&sha=master')
branch_master = branch_master.json()

commits_master = [e['commit']['message'] for e in branch_master]

branch_3_1_x = requests.get('https://api.github.com/repos/interlegis/sapl/commits?per_page=70&sha=3.1.x')
branch_3_1_x = branch_3_1_x.json()

commits_3_1_x = [(e['commit']['message'], {'sha':e['sha'], 'data':e['commit']['author']['date']}) for e in branch_3_1_x]

print("\nCommits que estão em 3.1.x, mas não em master:\n")

# retira os \r para evitar bugs
commits_master = [commit.replace('\r', '') for commit in commits_master]

for c, s in commits_3_1_x:
    # retira os \r para evitar bugs
    c = c.replace('\r', '')
    if (c not in commits_master) and ('Release' not in c):
        print('---------------------------------------------------------------------')
        print('Data: ' + s['data'][:10])
        print(s['sha'][:7] + ' -> ' + c)

print('---------------------------------------------------------------------')
        
