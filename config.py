THREADS = 32
MIN_INFLUENCE_SUPPORT = 10

CHARCOAL_ID = "M15"

PROCESSED_DATA_PATH = "tmp/data_processed.csv"


POACEAE_FEATURES = ['M15',
            #'Juniperus',
            #'Larix',
            'Picea',
            'Pinus',
            #'Alnus',
            'Betula',
            #'Fraxinus',
            #'Populus',
            'Quercus',
            #'Salix',
            'Ulmus',
            'Ambrosia',
            'Artemesia',
            #'Asteraceae',
            'Chenopodiaceae',
            'Cyperaceae',
            #'Myrica',
            'Poaceae',
            #'Typha',
            #'Aquatics'
            ]

FEATURES = ['M15',
            'Juniperus',
            'Larix',
            'Picea',
            'Pinus',
            'Alnus',
            'Betula',
            'Fraxinus',
            'Populus',
            'Quercus',
            'Salix',
            'Ulmus',
            'Ambrosia',
            'Artemesia',
            'Asteraceae',
            'Chenopodiaceae',
            'Cyperaceae',
            'Myrica',
            'Poaceae',
            'Typha',
            'Aquatics'
            ]


FEATURES = POACEAE_FEATURES

TARGETS = FEATURES

DISCARD_POLLEN = ['Abies',
                  "Tsuga",
                  "Acer",
                  "Carpinus",
                  "Corylus",
                  "Nyssa",
                  "Tilia",
                  "Agoseris",
                  "Brassicaceae",
                  "Carya",
                  "Epilobium",
                  "Ericaceae",
                  "Galium",
                  "Lycopod",
                  "Phytolithe",
                  "Rosaceae",
                  "Thalictrum",
                  "Spore monolete",
                  "Spore trilete",
                  "Sarcobatus"]

DISCRETIZATION_TRESHOLDS = [0]

MIN_SUPPORT = 1

DEBUG = False