from flask import Flask, send_file, render_template_string, redirect, url_for
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from io import BytesIO

app = Flask(__name__)

# ----------------------------
# Key Card Generation Functions
# ----------------------------

def generate_key_card():
    positions = list(range(25))
    random.shuffle(positions)
    
    # Partition positions into groups:
    group1 = positions[:3]            # Group 1: 3 cells common green (both sides)
    remaining = positions[3:]
    group2 = remaining[:6]            # Group 2: 6 cells: side A = green (non-common)
    remaining = remaining[6:]
    group3 = remaining[:3]            # Group 3: 3 cells: side A = black
    group4 = remaining[3:]            # Group 4: 13 cells: side A = beige
    assert len(group1) == 3 and len(group2) == 6 and len(group3) == 3 and len(group4) == 13

    sideA = {}
    sideB = {}

    # Assign colors for side A:
    for pos in group1 + group2:
        sideA[pos] = "green"
    for pos in group3:
        sideA[pos] = "black"
    for pos in group4:
        sideA[pos] = "beige"

    # Assign colors for side B:
    # Group 1: common green.
    for pos in group1:
        sideB[pos] = "green"
    # Group 2: randomly decide how many are black (0 to 2); rest become beige.
    x2 = random.randint(0, 2)
    group2_black = random.sample(group2, x2)
    for pos in group2:
        sideB[pos] = "black" if pos in group2_black else "beige"
    # Group 3: assign a random permutation of ["black", "green", "beige"].
    colors_group3 = ["black", "green", "beige"]
    random.shuffle(colors_group3)
    for pos, color in zip(group3, colors_group3):
        sideB[pos] = color
    # Group 4: fill in so that overall side B gets 9 green and 3 black.
    greens_so_far = 3 + colors_group3.count("green")  # Group1 provides 3 greens.
    needed_green = 9 - greens_so_far
    blacks_so_far = x2 + colors_group3.count("black")
    needed_black = 3 - blacks_so_far
    needed_beige = 13 - (needed_green + needed_black)
    group4_colors = (["green"] * needed_green) + (["black"] * needed_black) + (["beige"] * needed_beige)
    assert len(group4_colors) == 13
    random.shuffle(group4_colors)
    for pos, color in zip(group4, group4_colors):
        sideB[pos] = color

    # Build 5x5 grids.
    gridA, gridB = [], []
    for i in range(5):
        rowA, rowB = [], []
        for j in range(5):
            pos = i * 5 + j
            rowA.append(sideA[pos])
            rowB.append(sideB[pos])
        gridA.append(rowA)
        gridB.append(rowB)
    return gridA, gridB

def grid_to_numeric(grid, mapping):
    """Convert a grid of color strings into a numeric NumPy array."""
    return np.array([[mapping[cell] for cell in row] for row in grid])

# ----------------------------
# Global Data and Heatmap Functions
# ----------------------------

# Define our color mapping: beige -> 0, green -> 1, black -> 2.
mapping = {"beige": 0, "green": 1, "black": 2}
cmap = ListedColormap(["beige", "green", "black"])

# Generate the key card once when the server starts.
global_gridA, global_gridB = generate_key_card()
numericA = grid_to_numeric(global_gridA, mapping)
numericB = grid_to_numeric(global_gridB, mapping)

def create_heatmap_image(numeric_grid):
    """Generate a PNG image (in a BytesIO buffer) from a numeric grid."""
    plt.figure(figsize=(4, 4))
    plt.imshow(numeric_grid, cmap=cmap)
    plt.axis("off")
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close()
    buf.seek(0)
    return buf

# ----------------------------
# Flask Templates
# ----------------------------

# 1) Homepage: 8-bit style, no scrolling, “Codenames” theme
index_html = """
<!doctype html>
<html>
<head>
  <title>Codenames Duet - Home</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Tailwind CSS -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.js"></script>
  <!-- Google Font: Press Start 2P for retro style -->
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
  <style>
    /* Make sure we have no scrollbars and full viewport usage */
html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden; /* hides any scrollbar */
}

body {
    font-family: 'Press Start 2P', cursive;
    position: relative;
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    background: url('{{ url_for("static", filename="background.jpeg") }}') center/cover no-repeat fixed;
    color: #fff;
}

body::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.3); /* 20% white tint */
    pointer-events: none; /* Ensures interactions with elements underneath */
    z-index: 0;
}

.container {
    position: relative;
    z-index: 1; /* Ensures content appears above the tinted background */
}

.main-content {
    text-align: center;
    margin-top: 2rem;
}

.main-content h1 {
    font-size: 2rem;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 0 #000;
}

    .buttons {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-top: 2rem;
    }
    .btn-8bit {
      background-color: #FF6347;
      color: #fff;
      padding: 0.75rem 1.5rem;
      border: 2px solid #000;
      text-decoration: none;
      display: inline-block;
      transition: transform 0.2s;
      text-shadow: 1px 1px 0 #000;
    }
    .btn-8bit:hover {
      transform: scale(1.05);
      background-color: #E74C3C;
    }
    footer {
      text-align: center;
      margin-bottom: 1rem;
    }
    .social-links a {
      margin: 0 0.5rem;
      text-decoration: none;
      color: #fff;
    }
    .social-links a:hover {
      color: #ffea00;
    }
  </style>
</head>
<body>
  <div class="main-content">
    <h1>Codenames Duet</h1>
    <p style="font-size: 0.9rem;">
      A retro twist on your favorite cooperative spy game
    </p>

    <div class="buttons">
      <a href="/player1" class="btn-8bit">Player 1</a>
      <a href="/player2" class="btn-8bit">Player 2</a>
      <a href="/both" class="btn-8bit">Both Views</a>
      <a href="/regenerate" class="btn-8bit" style="font-size: 0.8rem;">Generate New Key Card</a>
    </div>
  </div>

  <footer>
    <div class="social-links">
      <a href="#" target="_blank">Facebook</a>|
      <a href="#" target="_blank">Instagram</a>|
      <a href="#" target="_blank">Twitter</a>
    </div>
    <p style="font-size: 0.7rem;">© 2025 CodenamesDuet - All Rights Reserved</p>
  </footer>
</body>
</html>
"""

# 2) Player View Template (Player 1 or Player 2)
player_html = """
<!doctype html>
<html>
<head>
  <title>Player {{ player }} - Codenames Duet</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Tailwind CSS -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.js"></script>
  <!-- Google Font: Press Start 2P for retro style -->
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden; /* no scrolling */
    }
    body {
      font-family: 'Press Start 2P', cursive;
      background: url('{{ url_for("static", filename="background.jpeg") }}') center/cover no-repeat fixed;
      color: #fff;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
    }
    .content {
      margin-top: 2rem;
      text-align: center;
    }
    h1 {
      font-size: 1.5rem;
      margin-bottom: 1rem;
      text-shadow: 2px 2px 0 #000;
    }
    .card-image {
      margin: 1rem auto;
      border: 3px solid #000;
      display: inline-block;
    }
    .buttons {
      display: flex;
      gap: 1rem;
      justify-content: center;
      margin: 1rem;
    }
    .btn-8bit {
      background-color: #FF6347;
      color: #fff;
      padding: 0.5rem 1rem;
      border: 2px solid #000;
      text-decoration: none;
      text-shadow: 1px 1px 0 #000;
      transition: transform 0.2s;
    }
    .btn-8bit:hover {
      transform: scale(1.05);
      background-color: #E74C3C;
    }
    footer {
      text-align: center;
      margin-bottom: 1rem;
    }
    .social-links a {
      margin: 0 0.5rem;
      text-decoration: none;
      color: #fff;
    }
    .social-links a:hover {
      color: #ffea00;
    }
  </style>
</head>
<body>
  <div class="content">
    <h1>Player {{ player }} View</h1>
    <p style="font-size: 0.9rem;">Codenames Duet Key Card</p>
    <div class="card-image">
      <img src="/player{{ player }}_image" alt="Player {{ player }} Key Card">
    </div>
    <div class="buttons">
      <a href="/" class="btn-8bit">Back</a>
      <a href="/regenerate" class="btn-8bit">New Card</a>
    </div>
  </div>

  <footer>
    <div class="social-links">
      <a href="#" target="_blank">Facebook</a>|
      <a href="#" target="_blank">Instagram</a>|
      <a href="#" target="_blank">Twitter</a>
    </div>
    <p style="font-size: 0.7rem;">© 2025 CodenamesDuet - All Rights Reserved</p>
  </footer>
</body>
</html>
"""

# 3) Both Views Template
both_html = """
<!doctype html>
<html>
<head>
  <title>Both Views - Codenames Duet</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Tailwind CSS -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.js"></script>
  <!-- Google Font: Press Start 2P for retro style -->
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
  <style>
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden; /* no scrolling */
    }
    body {
      font-family: 'Press Start 2P', cursive;
      background: url('{{ url_for("static", filename="background.jpeg") }}') center/cover no-repeat fixed;
      color: #fff;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
    }
    .content {
      margin-top: 2rem;
      text-align: center;
    }
    h1 {
      font-size: 1.5rem;
      margin-bottom: 1rem;
      text-shadow: 2px 2px 0 #000;
    }
    .grid-cards {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      justify-content: center;
      margin: 1rem 0;
    }
    .card-block {
      border: 3px solid #000;
      display: inline-block;
      background: #333;
      padding: 0.5rem;
    }
    .card-block img {
      display: block;
    }
    .buttons {
      display: flex;
      gap: 1rem;
      justify-content: center;
      margin: 1rem;
    }
    .btn-8bit {
      background-color: #FF6347;
      color: #fff;
      padding: 0.5rem 1rem;
      border: 2px solid #000;
      text-decoration: none;
      text-shadow: 1px 1px 0 #000;
      transition: transform 0.2s;
    }
    .btn-8bit:hover {
      transform: scale(1.05);
      background-color: #E74C3C;
    }
    footer {
      text-align: center;
      margin-bottom: 1rem;
    }
    .social-links a {
      margin: 0 0.5rem;
      text-decoration: none;
      color: #fff;
    }
    .social-links a:hover {
      color: #ffea00;
    }
  </style>
</head>
<body>
  <div class="content">
    <h1>Both Perspectives</h1>
    <p style="font-size: 0.9rem;">Codenames Duet Key Cards</p>
    <div class="grid-cards">
      <div class="card-block">
        <p style="font-size: 0.75rem;">Player 1</p>
        <img src="/player1_image" alt="Player 1 Key Card">
      </div>
      <div class="card-block">
        <p style="font-size: 0.75rem;">Player 2 (Unrotated)</p>
        <img src="/player2_image_unrotated" alt="Player 2 Key Card">
      </div>
      <div class="card-block">
        <p style="font-size: 0.75rem;">Player 2 (Rotated)</p>
        <img src="/player2_image" alt="Player 2 Key Card Rotated">
      </div>
    </div>
    <div class="buttons">
      <a href="/" class="btn-8bit">Back</a>
      <a href="/regenerate" class="btn-8bit">New Card</a>
    </div>
  </div>

  <footer>
    <div class="social-links">
      <a href="#" target="_blank">Facebook</a>|
      <a href="#" target="_blank">Instagram</a>|
      <a href="#" target="_blank">Twitter</a>
    </div>
    <p style="font-size: 0.7rem;">© 2025 CodenamesDuet - All Rights Reserved</p>
  </footer>
</body>
</html>
"""

# ----------------------------
# Flask Routes
# ----------------------------

@app.route("/")
def index():
    return render_template_string(index_html)

@app.route("/player1")
def player1():
    return render_template_string(player_html, player=1)

@app.route("/player2")
def player2():
    return render_template_string(player_html, player=2)

@app.route("/both")
def both():
    return render_template_string(both_html)

@app.route("/player1_image")
def player1_image():
    buf = create_heatmap_image(numericA)
    return send_file(buf, mimetype='image/png')

@app.route("/player2_image")
def player2_image():
    # Rotated 180° for Player 2
    rotated = np.rot90(numericB, 2)
    buf = create_heatmap_image(rotated)
    return send_file(buf, mimetype='image/png')

@app.route("/player2_image_unrotated")
def player2_image_unrotated():
    # Unrotated version of Player 2's grid
    buf = create_heatmap_image(numericB)
    return send_file(buf, mimetype='image/png')

@app.route("/regenerate")
def regenerate():
    global global_gridA, global_gridB, numericA, numericB
    global_gridA, global_gridB = generate_key_card()
    numericA = grid_to_numeric(global_gridA, mapping)
    numericB = grid_to_numeric(global_gridB, mapping)
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Initialize the key card when the server starts
    global_gridA, global_gridB = generate_key_card()
    numericA = grid_to_numeric(global_gridA, mapping)
    numericB = grid_to_numeric(global_gridB, mapping)
    app.run(port=8080, debug=True)
