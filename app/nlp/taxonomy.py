"""Safety concept taxonomy and keyword rules for OSHA incident processing."""

SAFETY_TAXONOMY = {
    "Equipment Isolation / LOTO": [
        "loto", "lockout", "tagout", "energized", "de-energize", "deenergize",
        "breaker", "power source", "maintenance", "servicing", "unguarded",
        "caught in machine", "jammed", "gear", "conveyor", "pulley", "blade"
    ],
    "Falls / Working at Height": [
        "fall", "fell", "roof", "ladder", "scaffold", "scaffolding", "elevated",
        "harness", "aerial lift", "platform", "structure", "edge", "floor opening",
        "railing", "skylight", "height"
    ],
    "Electrical Exposure": [
        "electrical", "electrocuted", "electrocution", "electric shock",
        "voltage", "wire", "power line", "live line", "arc flash", "conduit",
        "panel", "transformer", "energized wire"
    ],
    "Chemical Exposure": [
        "chemical", "toxic", "vapor", "gas", "acid", "inhalation", "spill",
        "fumes", "ammonia", "chlorine", "carbon monoxide", "hazard material",
        "poison", "exposure", "caustic"
    ],
    "Confined Space": [
        "confined space", "tank", "silo", "vault", "manhole", "trench", "pit",
        "vessel", "trench collapse", "excavation", "cave-in", "enclosed"
    ],
    "Vehicle / Struck-by": [
        "struck by", "struck-by", "struck", "vehicle", "forklift", "truck",
        "backed up", "run over", "traffic", "collision", "driver", "loader",
        "tractor", "highway", "trailer"
    ],
    "Lifting / Material Handling": [
        "crane", "hoist", "rigging", "suspended load", "overturn", "heavy object",
        "lifting", "pallet", "boom", "sling", "collapsed load", "dropped"
    ],
    "Fire / Ignition": [
        "fire", "explosion", "combustion", "flammable", "ignited", "burn",
        "blast", "sparks", "propane", "butane", "welding", "torch"
    ],
    "Pressure / Stored Energy": [
        "pressure", "pneumatic", "hydraulic", "compressed air", "stored energy",
        "burst", "release", "pipe explosion", "valve", "high pressure"
    ],
    "Loss of Containment": [
        "leak", "discharge", "containment", "rupture", "spill", "overflow",
        "pipeline rupture", "tank leak"
    ]
}

EQUIPMENT_KEYWORDS = [
    "forklift", "scaffold", "ladder", "crane", "conveyor", "saw", "truck",
    "tractor", "tank", "pump", "valve", "boiler", "press", "grinder",
    "generator", "compressor", "hoist", "trench", "pipe", "line"
]

CONSEQUENCE_KEYWORDS = [
    "fatality", "died", "fatal", "killed", "fracture", "broken", "amputation",
    "hospitalized", "burn", "asphyxiation", "laceration", "concussion",
    "paralysis", "electrocuted", "crushed"
]
