podatki = {'zw': 0, '23%': 0.22, '5%': 0.05, '8%': 0.08, '0%': 0.00}
paragon = [(120, 'zw'), (312.56, '23%'), (45.32, '23%'), (141.14, '8%'), (12.7, '23%')]

def policz_vat(paragon, podatki):
	nalezny_vat = 0
	for cena, podatek in paragon:
		vat = podatki[podatek]
		nalezny_vat = nalezny_vat + cena*vat
	return round(nalezny_vat,2)


pacjenci = [('Adaś', 74.2, 182), ('Zuzia', 63.7, 168), ('Krzysiek', 85.5, 175), ('Marta', 54.3, 160)]
def bmi(pacjenci):
	result = {}
	for imie, waga, wzrost in pacjenci:
		bmi = waga / ((wzrost)**2)
		print(bmi)
		result[imie] = bmi
	return result

print(bmi(pacjenci))