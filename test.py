import streamlit as st
import csv
import math
import io

def prebonus_from_score(score):
    if score > 3.30:
        return 12000000
    index = int(math.floor(score * 100))
    return 1000000 + (index * 33333)

def process_data(file_content):
    data_str = file_content.decode("utf-8")
    rows = list(csv.reader(io.StringIO(data_str)))

    header = rows[0]

    # Identify column indexes
    if "Agent name" in header:
        name_col = header.index("Agent name")
        total_touch_col = header.index("Total Touch")
        total_valid_touch_col = header.index("Total Valid Touch")
        done_col = header.index("Valid Done")
        vendor_share_col = header.index("Average vendor Share")
        # New columns for mistakes
        mistakes_percent_col = header.index("mistakes percent")
        mistakes_value_col = header.index("mistakes value")
        start_data = 1
    else:
        # If the CSV doesn't have headers or different headers, you must adjust accordingly.
        # This block is just a fallback; ideally, always provide the correct headers.
        name_col = 0
        total_touch_col = 1
        total_valid_touch_col = 2
        done_col = 3
        vendor_share_col = 4
        mistakes_percent_col = 6  # Adjust if needed
        mistakes_value_col = 7    # Adjust if needed
        start_data = 1

    agents = []
    pot = None

    for r in rows[start_data:]:
        # Ensure we have all required columns
        if len(r) <= mistakes_value_col:
            continue
        name = r[name_col].strip()
        if name == "":
            # Try to parse pot value if present
            if len(r) > 5 and r[5].strip() != "":
                try:
                    pot = float(r[5].strip())
                except:
                    pass
            continue

        try:
            total_touch = float(r[total_touch_col])
            valid_touch = float(r[total_valid_touch_col])
            done = float(r[done_col])
            vendor_share = float(r[vendor_share_col])
            mistakes_percent = float(r[mistakes_percent_col])
            mistakes_value = float(r[mistakes_value_col])
        except:
            continue

        agents.append({
            "name": name,
            "total_touch": total_touch,
            "valid_touch": valid_touch,
            "done": done,
            "vendor_share": vendor_share,
            "mistakes_percent": mistakes_percent,
            "mistakes_value": mistakes_value
        })

    if pot is None:
        raise ValueError("Pot value (F9) not found in CSV.")

    sum_total_touch = sum(a["total_touch"] for a in agents)
    sum_valid_touch = sum(a["valid_touch"] for a in agents)
    sum_done = sum(a["done"] for a in agents)
    sum_vendor_share = sum(a["vendor_share"] for a in agents)

    for a in agents:
        a["X"] = a["total_touch"] / sum_total_touch if sum_total_touch != 0 else 0
        a["Y"] = a["valid_touch"] / sum_valid_touch if sum_valid_touch != 0 else 0
        a["U"] = a["done"] / sum_done if sum_done != 0 else 0
        a["J"] = a["vendor_share"] / sum_vendor_share if sum_vendor_share != 0 else 0
        a["K"] = a["done"] / a["total_touch"] if a["total_touch"] != 0 else 0
        a["O"] = a["done"] / a["valid_touch"] if a["valid_touch"] != 0 else 0
        a["Score"] = a["X"]*2 + a["Y"]*3 + a["U"]*10 + a["J"]*7

    # Ranking by "done"
    sorted_by_done = sorted(agents, key=lambda x: x["done"], reverse=True)
    for rank, agent_data in enumerate(sorted_by_done, start=1):
        agent_data["B"] = rank
    done_ranks = {a["name"]: a["B"] for a in sorted_by_done}
    for a in agents:
        a["B"] = done_ranks[a["name"]]

    max_B = max(a["B"] for a in agents) if agents else 1
    max_K = max(a["K"] for a in agents) if agents else 1
    max_O = max(a["O"] for a in agents) if agents else 1

    # PreBonus calculation
    for a in agents:
        a["PreBonus"] = prebonus_from_score(a["Score"])

    # Distribution
    denom = 0.0
    for a in agents:
        val = ((max_B - a["B"] + 1)**1.5
               + (max_K - a["K"] + 1)**1.5
               + (max_O - a["O"] + 1)**1.5)
        denom += val

    for a in agents:
        numerator = ((max_B - a["B"] + 1)**1.5
                     + (max_K - a["K"] + 1)**1.5
                     + (max_O - a["O"] + 1)**1.5)
        dist = 0
        if denom != 0:
            dist = pot * (numerator / denom)
        a["Distribution"] = dist

        # Calculate the initial final bonus before mistakes deduction
        initial_final_bonus = a["PreBonus"] + a["Distribution"]

        # Deduct mistakes based on percentage
        percentage_deduction = initial_final_bonus * (a["mistakes_percent"] / 100)

        # Deduct mistakes value
        value_deduction = a["mistakes_value"]

        a["FinalBonus"] = initial_final_bonus - percentage_deduction - value_deduction

    # Updated column headers
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Agent",
        "Touch Score",          # X
        "Valid Touch Score",    # Y
        "Done Score",           # U
        "Vendor Share Score",   # J
        "Done Rank",            # B
        "Conversion Rate",      # K
        "Done Ratio",           # O
        "Score",
        "PreBonus",
        "Distribution",
        "Mistakes Percent",
        "Mistakes Value",
        "FinalBonus"
    ])
    for a in agents:
        writer.writerow([
            a["name"],
            a["X"],
            a["Y"],
            a["U"],
            a["J"],
            a["B"],
            a["K"],
            a["O"],
            a["Score"],
            a["PreBonus"],
            a["Distribution"],
            a["mistakes_percent"],
            a["mistakes_value"],
            a["FinalBonus"]
        ])

    return output.getvalue()

st.title("Agent Bonus Calculator Dashboard")

uploaded_file = st.file_uploader("Upload the input CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        result_csv = process_data(uploaded_file.getvalue())
        st.success("Processing complete! Click the button below to download the results.")
        st.download_button(
            label="Download Output CSV",
            data=result_csv,
            file_name="output.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error processing file: {e}")
