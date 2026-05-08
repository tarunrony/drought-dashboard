# Bangladesh Upazilas — GEE GAUL dataset থেকে filter করা হবে
AREAS = {
    "Sapahar Upazila": {
        "district": "Naogaon",
        "division": "Rajshahi",
        "coords": [88.45, 24.85],  # center [lon, lat]
    },
    "Porsha Upazila": {
        "district": "Naogaon",
        "division": "Rajshahi",
        "coords": [88.52, 24.89],
    },
    "Badalgachi Upazila": {
        "district": "Naogaon",
        "division": "Rajshahi",
        "coords": [88.62, 24.74],
    },
    # আরো upazila add করতে পারবে
}

DATE_RANGES = {
    "2020 Boro Season": ("2020-01-01", "2020-06-30"),
    "2021 Boro Season": ("2021-01-01", "2021-06-30"),
    "2022 Drought Period": ("2022-03-01", "2022-09-30"),
    "2023 Full Year": ("2023-01-01", "2023-12-31"),
    "Custom": None,
}
