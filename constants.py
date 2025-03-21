STATS = {
    0: {'name': 'AbilityPower', 'icon': '%i:scaleAP%', 'openingTag': '<scaleAP>', 'closingTag': '</scaleAP>'},
    1: {'name': 'Armor', 'icon': '%i:scaleArmor%', 'openingTag': '<scalearmor>', 'closingTag': '</scalearmor>'},
    2: {'name': 'Attack', 'icon': '%i:scaleAD%', 'openingTag': '<scaleAD>', 'closingTag': '</scaleAD>'},
    3: {'name': 'AttackSpeed', 'icon': '%i:scaleAS%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    4: {'name': 'AttackWindupTime', 'icon': '%i:scaleMR%', 'openingTag': '<scaleMR>', 'closingTag': '</scaleMR>'},
    5: {'name': 'MagicResist', 'icon': '%i:scaleMR%', 'openingTag': '<scaleMR>', 'closingTag': '</scaleMR>'},
    6: {'name': 'MoveSpeed', 'icon': '%i:scaleMS%', 'openingTag': '<scaleMS>', 'closingTag': '</scaleMS>'},
    7: {'name': 'CritChance', 'icon': '%i:scaleCrit%', 'openingTag': '<attention>', 'closingTag': '</attention>'},
    8: {'name': 'CritDamage', 'icon': '%i:scaleCritMult%', 'openingTag': '<scaleCritMult>', 'closingTag': '</scaleCritMult>'},
    9: {'name': 'CooldownReduction', 'icon': '%i:cooldown%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    10: {'name': 'AbilityHaste', 'icon': '%i:scaleHealth%', 'openingTag': '<scalehealth>', 'closingTag': '</scalehealth>'},
    11: {'name': 'MaxHealth', 'icon': '%i:scaleHealth%', 'openingTag': '<scalehealth>', 'closingTag': '</scalehealth>'},
    12: {'name': 'CurrentHealth', 'icon': '%i:scaleHealth%', 'openingTag': '<scalehealth>', 'closingTag': '</scalehealth>'},
    13: {'name': 'PercentMissingHealth', 'icon': '%i:scaleHealth%', 'openingTag': '<scalehealth>', 'closingTag': '</scalehealth>'},
    14: {'name': 'Unknown14', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    15: {'name': 'LifeSteal', 'icon': '%i:scaleLS%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    16: {'name': 'AdaptiveForce', 'icon': '%i:scaleAdaptiveForce%', 'openingTag': '<scaleadaptivedorce>', 'closingTag': '</scaleadaptivedorce>'},
    17: {'name': 'OmniVamp', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    18: {'name': 'PhysicalVamp', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    19: {'name': 'MagicPenetrationFlat', 'icon': '%i:scaleMPen%', 'openingTag': '<scaleMPen>', 'closingTag': '</scaleMPen>'},
    20: {'name': 'MagicPenetrationPercent', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    21: {'name': 'BonusMagicPenetrationPercent', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    22: {'name': 'MagicLethality', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    23: {'name': 'ArmorPenetrationFlat', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    24: {'name': 'ArmorPenetrationPercent', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    25: {'name': 'BonusArmorPenetrationPercent', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    26: {'name': 'PhysicalLethality', 'icon': '%i:scaleAPen%', 'openingTag': '<scaleLethality>', 'closingTag': '</scaleLethality>'},
    27: {'name': 'Tenacity', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    28: {'name': 'AttackRange', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    29: {'name': 'HealthRegenRate', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    30: {'name': 'ResourceRegenRate', 'icon': '%i:scalePARR%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    31: {'name': 'HealShieldPower', 'icon': '%i:scaleHealShield%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    32: {'name': 'Unknown32', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'},
    33: {'name': 'DodgeChance', 'icon': '%i:?%', 'openingTag': '<noscale>', 'closingTag': '</noscale>'}
}

STAT_TYPES = {
    1: 'base',
    2: 'bonus'
}

RESOURCE_TYPES = {
    0: 'mp',
    1: 'energy',
    2: 'none',
    3: 'shield',
    4: 'battlefury',
    5: 'dragonfury',
    6: 'rage',
    7: 'heat',
    8: 'gnarfury',
    9: 'ferocity',
    10: 'bloodwell',
    11: 'wind',
    12: 'ammo',
    13: 'moonlight',
    14: 'other',
    15: 'max'
}

REDIS_PREFIX = 'lolres'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379