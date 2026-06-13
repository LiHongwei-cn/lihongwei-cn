def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)

print(find_duplicates([1, 2, 3, 2, 4, 3, 5, 1, 6, 7, 8, 1]))
