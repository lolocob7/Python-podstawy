# teams = list("ABCDE")
        
def permutations(teams):
    if len(teams) == 0:
        return [[]]
    
    result = []
    n = len(teams)
    for _ in range(len(teams)-1):
        
        for i in range(n // 2):
            home = teams[i]
            away = teams[n - 1 - i]
            result.append((home, away))
        teams = [teams[0]] + teams[-1:] + teams[1:-1]   
            
    return result        