MINIMUMS: dict[int, int] = {
    1: 5,   # Associations & regulatory bodies
    2: 5,   # National distributors
    3: 8,   # Regional distributors
    4: 5,   # Manufacturers / OEMs
    5: 15,  # Contractors — hard minimum from pipeline spec
    6: 8,   # Maintenance & service companies
    7: 5,   # Wholesalers
    8: 5,   # Adjacent trades
}

CATEGORIES: list[int] = list(range(1, 9))
PE_CHECK_CATEGORIES: list[int] = [2, 3, 4]
PE_EMPLOYEE_THRESHOLD: int = 50
