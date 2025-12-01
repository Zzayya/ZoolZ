#!/usr/bin/env python3
"""
Name Variations and Pseudonyms Database
Maps common names to their variations for comprehensive people searches
"""

# Common name variations and nicknames
NAME_VARIATIONS = {
    # Male names
    "abraham": ["abe", "abram", "bram"],
    "albert": ["al", "bert", "bertie"],
    "alexander": ["alex", "al", "xander", "sandy", "lex"],
    "andrew": ["andy", "drew"],
    "anthony": ["tony", "ant"],
    "benjamin": ["ben", "benny", "benji"],
    "charles": ["charlie", "chuck", "chas", "chip"],
    "christopher": ["chris", "topher", "kit"],
    "daniel": ["dan", "danny"],
    "david": ["dave", "davy"],
    "donald": ["don", "donnie"],
    "edward": ["ed", "eddie", "ted", "teddy", "ned"],
    "eugene": ["gene"],
    "francis": ["frank", "fran"],
    "frederick": ["fred", "freddy", "rick"],
    "gerald": ["jerry", "gerry"],
    "gregory": ["greg"],
    "harold": ["hal", "harry"],
    "henry": ["hank", "harry"],
    "james": ["jim", "jimmy", "jamie"],
    "jason": ["jay", "jace"],
    "jeffrey": ["jeff"],
    "jerome": ["jerry"],
    "john": ["johnny", "jack", "jon"],
    "jonathan": ["jon", "jonny", "nathan"],
    "joseph": ["joe", "joey"],
    "joshua": ["josh"],
    "kenneth": ["ken", "kenny"],
    "lawrence": ["larry", "lance"],
    "leonard": ["leo", "len", "lenny"],
    "matthew": ["matt", "matty"],
    "michael": ["mike", "mikey", "mick"],
    "nathan": ["nate", "nat"],
    "nicholas": ["nick", "nicky", "klaus"],
    "patrick": ["pat", "paddy", "rick"],
    "peter": ["pete"],
    "philip": ["phil", "flip"],
    "raymond": ["ray"],
    "richard": ["rick", "ricky", "dick", "rich"],
    "robert": ["rob", "bob", "bobby", "robbie", "bert"],
    "ronald": ["ron", "ronnie"],
    "samuel": ["sam", "sammy"],
    "stephen": ["steve", "stevie"],
    "steven": ["steve", "stevie"],
    "theodore": ["theo", "ted", "teddy"],
    "thomas": ["tom", "tommy"],
    "timothy": ["tim", "timmy"],
    "vincent": ["vince", "vinny"],
    "walter": ["walt", "wally"],
    "william": ["will", "bill", "billy", "willy", "liam"],
    "zachary": ["zach", "zack"],

    # Female names
    "abigail": ["abby", "gail"],
    "alexandra": ["alex", "alexa", "sandra", "sandy", "lexi"],
    "amanda": ["mandy"],
    "amy": ["aimee"],
    "andrea": ["andy", "andi"],
    "angela": ["angie"],
    "barbara": ["barb", "barbie", "babs"],
    "carol": ["carrie"],
    "catherine": ["cathy", "kate", "katie", "kitty", "cate"],
    "christina": ["chris", "christie", "tina"],
    "christine": ["chris", "christie"],
    "deborah": ["debbie", "deb", "debby"],
    "diane": ["di"],
    "dorothy": ["dot", "dotty", "dottie"],
    "elizabeth": ["liz", "beth", "betsy", "betty", "eliza", "lizzie"],
    "emily": ["emma", "emmy"],
    "gabriella": ["gabby", "gaby", "ella"],
    "jacqueline": ["jackie", "jacqui"],
    "janet": ["jan"],
    "jennifer": ["jen", "jenny"],
    "jessica": ["jess", "jessie"],
    "judith": ["judy", "judi"],
    "kimberly": ["kim", "kimmy"],
    "linda": ["lin", "lindy"],
    "margaret": ["maggie", "meg", "peggy", "marge", "margie", "madge"],
    "maria": ["mary"],
    "mary": ["maria", "mae"],
    "melissa": ["mel", "missy", "lissa"],
    "michelle": ["mickey", "shell", "shelly"],
    "nancy": ["nan"],
    "natalie": ["nat", "natty"],
    "pamela": ["pam", "pammy"],
    "patricia": ["pat", "patty", "tricia", "trish"],
    "rebecca": ["becky", "becca"],
    "samantha": ["sam", "sammy"],
    "sandra": ["sandy"],
    "sarah": ["sara", "sally"],
    "sharon": ["shari", "sherry"],
    "stephanie": ["steph", "steffi"],
    "susan": ["sue", "suzie", "susie"],
    "teresa": ["terri", "terry", "tess"],
    "theresa": ["terri", "terry", "tess"],
    "victoria": ["vicky", "tori"],
    "virginia": ["ginny", "ginger"],
}


def get_name_variations(full_name: str) -> list:
    """
    Get all variations of a name including pseudonyms and nicknames.

    Args:
        full_name: Full name like "Samuel Johnson" or "William H Smith"

    Returns:
        List of full name variations:
        - "Samuel Johnson" → ["Samuel Johnson", "Sam Johnson", "Sammy Johnson"]
        - "William H Smith" → ["William H Smith", "Will H Smith", "Bill H Smith", "Billy H Smith"]
    """

    if not full_name:
        return []

    # Parse the name
    parts = full_name.strip().split()

    if len(parts) == 0:
        return []

    first_name = parts[0].lower()
    rest_of_name = " ".join(parts[1:])  # Last name + middle name/initial

    # Check if first name has variations
    if first_name not in NAME_VARIATIONS:
        return [full_name]  # No variations, return original

    # Get all variations
    variations = [first_name] + NAME_VARIATIONS[first_name]

    # Build full name variations
    full_variations = []
    for variant in variations:
        # Capitalize first letter
        variant_capitalized = variant.capitalize()

        if rest_of_name:
            full_variations.append(f"{variant_capitalized} {rest_of_name}")
        else:
            full_variations.append(variant_capitalized)

    return full_variations


def has_variations(name: str) -> bool:
    """
    Check if a name has known variations.

    Args:
        name: Full or first name

    Returns:
        True if variations exist
    """

    if not name:
        return False

    first_name = name.strip().split()[0].lower()
    return first_name in NAME_VARIATIONS


def get_variation_count(name: str) -> int:
    """
    Get count of variations for a name.

    Args:
        name: Full or first name

    Returns:
        Number of variations (including original)
    """

    variations = get_name_variations(name)
    return len(variations)


# Example usage for testing
if __name__ == "__main__":
    test_names = [
        "Samuel Johnson",
        "William H Smith",
        "Elizabeth Taylor",
        "John A Smith",
        "Christopher Lee"
    ]

    for name in test_names:
        variations = get_name_variations(name)
        print(f"\n{name}:")
        for v in variations:
            print(f"  - {v}")
