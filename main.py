import os
import json
import csv
import time 
import argparse
import dotenv
import textwrap
import googlemaps
import math

dotenv.load_dotenv()

def main():
    # argparse parser
    parser = argparse.ArgumentParser()

    # Required argument API key
    # key can be found in credentials
    # make sure Places API is enabled
    # and geocoding API
    parser.add_argument(
        "--google_api_key",

        default=os.environ.get("GOOGLE_API_KEY"),

        help="google project api key " + \
            "make sure places and geocode API " + 
            "is enabled.",
    )

    # Required argumnet places_location
    # filter the search results by location
    # i.e chicago 
    parser.add_argument(
        "--places_location",
        type=str,
        
        default=os.environ.get("PLACES_LOCATION"),

        help="filter the search results by location"
    )

    # Required argumnet places_type
    # filter the search results with valid place types
    # i.e restaurant accounting
    parser.add_argument('--places_type', 
        type=str,
        default=os.environ.get("PLACES_TYPE"),
        choices=[
            "accounting",
            "airport",
            "amusement_park",
            "aquarium",
            "art_gallery",
            "atm",
            "bakery",
            "bank",
            "bar",
            "beauty_salon",
            "bicycle_store",
            "book_store",
            "bowling_alley",
            "bus_station",
            "cafe",
            "campground",
            "car_dealer",
            "car_rental",
            "car_repair",
            "car_wash",
            "casino",
            "cemetery",
            "church",
            "city_hall",
            "clothing_store",
            "convenience_store",
            "courthouse",
            "dentist",
            "department_store",
            "doctor",
            "drugstore",
            "electrician",
            "electronics_store",
            "embassy",
            "fire_station",
            "florist",
            "funeral_home",
            "furniture_store",
            "gas_station",
            "gym",
            "hair_care",
            "hardware_store",
            "hindu_temple",
            "home_goods_store",
            "hospital",
            "insurance_agency",
            "jewelry_store",
            "laundry",
            "lawyer",
            "library",
            "light_rail_station",
            "liquor_store",
            "local_government_office",
            "locksmith",
            "lodging",
            "meal_delivery",
            "meal_takeaway",
            "mosque",
            "movie_rental",
            "movie_theater",
            "moving_company",
            "museum",
            "night_club",
            "painter",
            "park",
            "parking",
            "pet_store",
            "pharmacy",
            "physiotherapist",
            "plumber",
            "police",
            "post_office",
            "primary_school",
            "real_estate_agency",
            "restaurant",
            "roofing_contractor",
            "rv_park",
            "school",
            "secondary_school",
            "shoe_store",
            "shopping_mall",
            "spa",
            "stadium",
            "storage",
            "store",
            "subway_station",
            "supermarket",
            "synagogue",
            "taxi_stand",
            "tourist_attraction",
            "train_station",
            "transit_station",
            "travel_agency",
            "university",
            "veterinary_care",
            "zoo"
        ],
        help='filter the search results with valid place types.', 
    )


    # Required argument place_results
    # Limit the search to a specific number
    parser.add_argument(
        "--places_max_result",
        type=int,

        default=os.environ.get("PLACES_MAX_RESULT"),

        help="Limit the search to a specific number"
    )
    
    # Parse arguments
    args = parser.parse_args()

    # Google maps client
    client = googlemaps.Client(args.google_api_key)
    client_max_results = args.places_max_result
    geocode = client.geocode(address=args.places_location)[0]["geometry"]["location"]

    hop_count = 5
    jump_distance_km = 0.5

    print(f"Covering {pow(hop_count*jump_distance_km, 2)*4}km^2")
    jump_latitude_deg = jump_distance_km/110.574
    # In-exact but calculating it accurately is hard
    jump_longitude_deg = jump_distance_km/(111.320*math.cos(jump_latitude_deg))
    
    # token for getting the next results
    page_token = None
    result_counter = 0

    visited_placeid_set = set()
    
    # get complete details of each place
    with open(f"results/{args.places_location}_{args.places_type}.tsv", "wt", newline="", encoding="utf-8") as tsv:
        tsv_write = csv.writer(tsv, delimiter="\t")

        # write columns
        tsv_write.writerow([
            "0_ID",
            "Name",
            "Address",
            "Phone Number",
            "Website",
            "Monday Hours",
            "Tuesday Hours",
            "Wednesday Hours",
            "Thursday Hours",
            "Friday Hours",
            "Saturday Hours",
            "Sunday Hours"
        ])
    
        for latDiff in range(-hop_count, +hop_count):
            for lngDiff in range(-hop_count, +hop_count):
                local_counter = 0
                # if counter is less than max results
                while result_counter <= client_max_results:
            
                    
                    # delay the next request
                    # sometimes google server needs
                    # time to serve the next page token
                    time.sleep(2)

                    location = f"{geocode['lat']+latDiff*jump_latitude_deg},{geocode['lng']+lngDiff*jump_longitude_deg}"
                    print(f"Running search: {location} {(latDiff+hop_count)*hop_count+(hop_count+lngDiff)} until {hop_count*hop_count*4}")
                    places = client.places(

                        # type i.e restaurant
                        type=args.places_type,

                        # lat ang long from geocode
                        location=f"{geocode['lat']+latDiff*jump_latitude_deg},{geocode['lng']+lngDiff*jump_longitude_deg}",
                        extra_params={'rank_by': 'distance'},
                        page_token=page_token
                    )

                    # assign next page token
                    page_token = places.get("next_page_token")

                    # for each places results 
                    for place in places["results"]:
                        
                        # skip if the business if closed
                        if place["business_status"] != "OPERATIONAL":
                            continue

                        place_id = place["place_id"]
                        # Skip place already visited
                        if place_id in visited_placeid_set:
                            print(f"Already encountered {place_id}")
                            time.sleep(0.05)
                            continue

                        visited_placeid_set.add(place_id)
                        result_counter += 1
                        local_counter += 1
                        # request for specific details of a place
                        time.sleep(0.05)
                        place_details = client.place(place_id=place_id,
                            fields=[
                                "name",
                                "formatted_address",
                                "opening_hours",
                                "formatted_phone_number",
                                "website"
                            ]
                        )

                        # place details
                        place = place_details["result"]
                        print(f"{result_counter}: {place['name']}")

                        # write initial fields 
                        tsv_fields = [
                            place_id,
                            place.get("name") or "n/a",
                            place.get("formatted_address") or "n/a",
                            place.get("formatted_phone_number") or "n/a",
                            place.get("website") or "n/a"
                        ]

                        


                        # parse and clean opening hours
                        opening_fields = []
                        opening_hours = place.get("opening_hours")
                        
                        # container for days
                        days = [
                            "Monday", 
                            "Tuesday", 
                            "Wednesday", 
                            "Thursday", 
                            "Friday", 
                            "Saturday", 
                            "Sunday"
                        ]

                        # we only parse if it exists
                        if opening_hours:
                            # loop through each day
                            for index, day in enumerate(days):          
                                try:
                                    period = opening_hours["periods"][index]
                                    
                                    
                                    # get opening closing periods
                                    _open = period.get("open")
                                    
                                    _close = period.get("close")
                                    
                                    # 2200 -> 22:00
                                    opening_hour = ":".join(textwrap.wrap(_open["time"], 2))
                                    if _close is None:    
                                        closing_hour = ""                            
                                    else:
                                        closing_hour = ":".join(textwrap.wrap(_close["time"], 2))

                                        
                                    opening_fields.append(f"{opening_hour} - {closing_hour}")
                                
                                except IndexError:
                                    # Fallback if index of day
                                    # does not exist
                                    opening_fields.append("n/a")

                                
                        else:
                            # fallback if no hours specified
                            opening_fields = ["n/a" for x in days]


                        
                        # combine fields
                        tsv_fields = tsv_fields + opening_fields
                        
                        # finally write the rows
                        tsv_write.writerow(tsv_fields)
                        tsv.flush()

                    if page_token is None:
                        break
                    else:
                        print(f"Loading next page {page_token}...")

        # end
        tsv.close()

if __name__ == "__main__":
    main()
