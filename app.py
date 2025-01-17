'''
This code does not work without:
1. Inserting key for Flask (Line 11 in app.py)
2. Inserting MySQL authentication details (Line 5-7 in db_operations.py)
'''
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from db_operations import db_operations
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'secret_key' # INSERT KEY HERE
bcrypt = Bcrypt(app)
db_ops = db_operations()

# Utility functions
def logged_in():
    return 'dm_id' in session

def login_required(func):
    def wrapper(*args, **kwargs):
        if not logged_in():
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Routes
@app.route('/')
def index():
    if logged_in():
        return redirect(url_for('dashboard'))
    
    campaign = db_ops.select_query('SELECT * FROM campaign')
    dm = db_ops.select_query('SELECT * FROM dm')
    encounter = db_ops.select_query('SELECT * FROM encounter')
    encounter_tracker = db_ops.select_query('SELECT * FROM encounter_tracker')
    inventory = db_ops.select_query('SELECT * FROM inventory')
    items = db_ops.select_query('SELECT * FROM items')
    monster = db_ops.select_query('SELECT * FROM monster')
    npc = db_ops.select_query('SELECT * FROM npc')
    player = db_ops.select_query('SELECT * FROM player')

    return render_template('index.html', campaign=campaign, dm=dm, encounter=encounter,
                            encounter_tracker=encounter_tracker, inventory=inventory,
                            items=items, monster=monster, npc=npc, player=player, logged_in=logged_in)
    # return render_template('index.html', logged_in=logged_in)

# Login/Registration
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['Password']
        dm = db_ops.select_query_params('SELECT * FROM dm WHERE dm_Username = %s', [username])
        if dm and bcrypt.check_password_hash(dm[0][2], password):
            session['dm_id'] = dm[0][0]
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.')
    return render_template('login.html', logged_in=logged_in)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['Username']
        password = bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')
        db_ops.transaction_query([
            ('INSERT INTO dm (dm_Username, dm_Password) VALUES (%s, %s)', [username, password],)
            ])
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', logged_in=logged_in)

@app.route('/logout')
@login_required
def logout():
    session.pop('dm_id', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# DM Dashboard (View All Campaigns)
@app.route('/dashboard')
@login_required
def dashboard():
    dm_id = session['dm_id']
    campaigns = db_ops.select_query_params('SELECT * FROM campaign WHERE dmID = %s', [dm_id])
    return render_template('dashboard.html', campaigns=campaigns, logged_in=logged_in)

# Add Campaign
@app.route('/campaign/add', methods=['GET', 'POST'])
@login_required
def add_campaign():
    if request.method == 'POST':
        name = request.form['name']
        meeting_day = request.form['meeting_day']
        meeting_time = request.form['meeting_time']
        dm_id = session['dm_id']
        is_active = request.form.get('is_active', '1') == '1'  # Defaulting to True if not provided

        db_ops.transaction_query([
            ('INSERT INTO campaign (dmID, name, meeting_day, meeting_time, is_active) VALUES (%s, %s, %s, %s, %s)',
            [dm_id, name, meeting_day, meeting_time, is_active],)
            ])
        flash('Campaign created successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_campaign.html', logged_in=logged_in)


# Update Campaign
@app.route('/campaign/<int:campaign_id>/update', methods=['GET', 'POST'])
@login_required
def update_campaign(campaign_id, campaign_name):
    campaign = db_ops.select_query_params('SELECT * FROM campaign WHERE campaignID = %s', [campaign_id])[0]
    if request.method == 'POST':
        name = request.form['Campaign Name']
        meeting_day = request.form['Meeting Day']
        meeting_time = request.form['Meeting Time']
        db_ops.transaction_query([
            ('UPDATE campaign SET name = %s, meeting_day = %s, meeting_time = %s WHERE campaignID = %s',
            [name, meeting_day, meeting_time, campaign_id],)
        ])
        flash('Campaign updated successfully!')
        return redirect(url_for('dashboard'))
    return render_template('update_campaign.html', campaign_id=campaign, logged_in=logged_in)

# Add Player to Campaign
@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/add_player', methods=['GET', 'POST'])
@login_required
def add_player(campaign_id, campaign_name):
    if request.method == 'POST':
        player_name = request.form['Player Name']
        player_class = request.form['Class']
        player_subclass = request.form['Subclass']
        player_background = request.form['Background']
        player_level = int(request.form['Level'])
        player_exp = int(request.form['Exp'])
        player_gold = float(request.form['Gold'])
        db_ops.transaction_query([(
            'INSERT INTO player (campaignID, player_name, player_class, player_subclass, player_background, player_level, player_expTotal, player_gold) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            [campaign_id, player_name, player_class, player_subclass, player_background, player_level, player_exp, player_gold],)
            ])
        flash('Player added successfully!')
        return redirect(url_for('view_players', 
                                campaign_id=campaign_id, 
                                campaign_name=campaign_name))
    return render_template('add_player.html',
                            campaign_id=campaign_id, 
                            campaign_name=campaign_name,
                            logged_in=logged_in)

# View Players in Campaign
@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/players')
@login_required
def view_players(campaign_id, campaign_name):
        players = db_ops.select_query_params('SELECT * FROM player WHERE campaignID = %s', [campaign_id])
        return render_template('view_players.html', 
                                players=players, 
                                logged_in=logged_in,
                                campaign_id=campaign_id, 
                                campaign_name=campaign_name)

# Update Player
@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/player/<int:player_id>/update', methods=['GET', 'POST'])
@login_required
def update_player(campaign_id, campaign_name, player_id):
    player = db_ops.select_query_params('SELECT * FROM Player WHERE playerID = %s', [player_id])[0]
    items = db_ops.select_query('SELECT * FROM Items')
    inventory = db_ops.select_query_params('''
        SELECT Items.itemID, Items.item_name, Items.item_type, 
               Items.damage_type, Items.damage_die, Items.item_cost 
        FROM Items 
        INNER JOIN Inventory ON Items.itemID = Inventory.itemID 
        WHERE Inventory.playerID = %s
    ''', [player_id])

    if request.method == 'POST':
        if 'assign_item' in request.form:
            item_id = request.form.get('item_id')
            if item_id:
                db_ops.transaction_query([
                    ('INSERT INTO Inventory (playerID, itemID) VALUES (%s, %s)', 
                    [player_id, item_id],)
                ])
                flash('Item successfully assigned to the player.')
            else:
                flash('No item selected.')
            return redirect(request.url)

        if 'remove_item' in request.form:
            remove_item_id = request.form.get('remove_item_id')
            if remove_item_id:
                db_ops.transaction_query([(
                    'DELETE FROM Inventory WHERE playerID = %s AND itemID = %s', 
                    [player_id, remove_item_id],
                )])
                flash('Item successfully removed from the player.')
            else:
                flash('No item selected to remove.')
            return redirect(request.url)

        player_name = request.form['Player Name']
        player_class = request.form['Class']
        player_subclass = request.form['Subclass']
        player_background = request.form['Background']
        player_level = request.form['Level']
        player_exp = request.form['Exp']
        player_gold = request.form['Gold']

        db_ops.transaction_query([(
            '''
            UPDATE Player 
            SET player_name = %s, player_class = %s, player_subclass = %s, 
                player_background = %s, player_level = %s, 
                player_expTotal = %s, player_gold = %s
            WHERE playerID = %s
            ''',
            [player_name, player_class, player_subclass, player_background,
             player_level, player_exp, player_gold, player_id],
        )])
        flash('Player updated successfully!')

        return redirect(url_for('view_players', campaign_id=campaign_id, campaign_name=campaign_name))

    return render_template('update_player.html', 
                           player=player, 
                           items=items, 
                           inventory=inventory, 
                           campaign_id=campaign_id, 
                           campaign_name=campaign_name, 
                           logged_in=logged_in)


# Add Item
@app.route('/item/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        item_name = request.form['Item Name']
        item_type = request.form['Item Type']
        damage_type = request.form['Damage Type']
        damage_die = request.form['Damage Die']
        item_cost = int(request.form['Item Cost'])
        db_ops.transaction_query(
            [
            ('INSERT INTO items (item_name, item_type, damage_type, damage_die, item_cost) VALUES (%s, %s, %s, %s, %s)',
            [item_name, item_type, damage_type, damage_die, item_cost],)
            ]
        )
        flash('Item added successfully!')
        return redirect(url_for('view_items'))
    return render_template('add_item.html', logged_in=logged_in)

# View Items
@app.route('/items', methods=['GET', 'POST'])
@login_required
def view_items():
    damage_type = None # if no type is selected
    query = 'SELECT * FROM items'
    params = []

    if request.method == 'POST':
        damage_type = request.form.get('damage_type', '')
        if damage_type:  # Only add filter if user selects damange type
            query += ' WHERE damage_type = %s'
            params.append(damage_type)

    items = db_ops.select_query_params(query, params)
    return render_template('view_items.html', items=items, logged_in=logged_in, selected_damage_type=damage_type)


# View Encounters
@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/encounters')
@login_required
def view_encounters(campaign_id, campaign_name):
    encounters = db_ops.select_query_params('''
        SELECT * FROM Encounter WHERE campaignID = %s
    ''', [campaign_id])
    
    return render_template('view_encounters.html', encounters=encounters, logged_in=logged_in,
                            campaign_id=campaign_id, campaign_name=campaign_name)

# Add Encounters in Campaign
@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/encounter/add', methods=['GET', 'POST'])
@login_required
def add_encounter(campaign_id, campaign_name):
    if request.method == 'POST':
        location_name = request.form['Location Name']
        encounter_date = request.form['Encounter Date']
        exp_gained = int(request.form['EXP Gained'])
        loot_gained = request.form['Loot Gained']
        encounter_rating = 0
        db_ops.transaction_query([('''
            INSERT INTO encounter (campaignID, location_name, encounter_date, exp_gained, loot_gained, encounter_rating)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', [campaign_id, location_name, encounter_date, exp_gained, loot_gained, encounter_rating],)])
        flash('Encounter added successfully!')
        return redirect(url_for('view_encounters', campaign_id=campaign_id, campaign_name=campaign_name))
    
    return render_template('add_encounter.html', campaign_id=campaign_id, campaign_name=campaign_name, logged_in=logged_in)

@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/encounter/<int:encounter_id>/update', methods=['GET', 'POST'])
@login_required
def update_encounter(campaign_id, campaign_name, encounter_id):
    encounter = db_ops.select_query_params('SELECT * FROM Encounter WHERE encounterID = %s', [encounter_id])[0]
    
    # Fetch monsters assigned to this encounter
    encounter_monsters = db_ops.select_query_params('''
        SELECT Monster.monsterID, Monster.monster_name, Monster.monster_type, 
               Monster.monster_exp, Monster.monster_rating 
        FROM Monster 
        INNER JOIN Encounter_Tracker ON Monster.monsterID = Encounter_Tracker.monsterID 
        WHERE Encounter_Tracker.encounterID = %s
    ''', [encounter_id])
    
    # Fetch all monsters for assigning new ones
    all_monsters = db_ops.select_query('SELECT * FROM Monster')

    def update_encounter_rating(encounter_id):
        """Recalculates and updates the encounter rating as the average of the monster ratings."""
        ratings = db_ops.select_query_params('''
            SELECT AVG(Monster.monster_rating)
            FROM Monster
            INNER JOIN Encounter_Tracker ON Monster.monsterID = Encounter_Tracker.monsterID
            WHERE Encounter_Tracker.encounterID = %s
        ''', [encounter_id])[0][0]  # 
        ratings = ratings or 0  # If there are no monster or it's a new encounter
        db_ops.transaction_query([(
            'UPDATE Encounter SET encounter_rating = %s WHERE encounterID = %s',
            [ratings, encounter_id],
        )])

    if request.method == 'POST':
        if 'assign_monster' in request.form:
            monster_id = request.form.get('monster_id')
            if monster_id:
                db_ops.transaction_query([(
                    'INSERT INTO Encounter_Tracker (encounterID, monsterID) VALUES (%s, %s)',
                    [encounter_id, monster_id],
                )])
                update_encounter_rating(encounter_id)  
                flash('Monster successfully assigned to the encounter.')
            else:
                flash('No monster selected.')
            return redirect(request.url)
        
        if 'remove_monster' in request.form:
            remove_monster_id = request.form.get('remove_monster_id')
            if remove_monster_id:
                db_ops.transaction_query([(
                    'DELETE FROM Encounter_Tracker WHERE encounterID = %s AND monsterID = %s',
                    [encounter_id, remove_monster_id],
                )])
                update_encounter_rating(encounter_id)  
                flash('Monster successfully removed from the encounter.')
            else:
                flash('No monster selected to remove.')
            return redirect(request.url)

        location_name = request.form['Location Name']
        encounter_date = request.form['Encounter Date']
        exp_gained = request.form['EXP Gained']
        loot_gained = request.form['Loot Gained']

        db_ops.transaction_query([(
            '''
            UPDATE Encounter 
            SET location_name = %s, encounter_date = %s, exp_gained = %s, 
                loot_gained = %s
            WHERE encounterID = %s
            ''',
            [location_name, encounter_date, exp_gained, loot_gained, encounter_id],
        )])
        flash('Encounter details updated successfully!')
        return redirect(url_for('view_encounters', campaign_id=campaign_id, campaign_name=campaign_name))

    return render_template(
        'update_encounter.html',
        encounter=encounter,
        encounter_monsters=encounter_monsters,
        all_monsters=all_monsters,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        logged_in=logged_in
    )


# View Monsters
@app.route('/view_monsters', methods=['GET', 'POST'])
@login_required
def view_monsters():
    monster_type = None  # If user is not filtering
    query = 'SELECT * FROM Monster'
    params = []

    if request.method == 'POST':
        monster_type = request.form.get('monster_type', '')
        if monster_type:
            query += ' WHERE monster_type = %s'
            params.append(monster_type)

    monsters = db_ops.select_query_params(query, params)
    return render_template('view_monsters.html', monsters=monsters, logged_in=logged_in, selected_monster_type=monster_type)


# Add Monsters
@app.route('/monster/add', methods=['GET', 'POST'])
@login_required
def add_monster():
    if request.method == 'POST':
        monster_name = request.form['Monster Name']
        monster_type = request.form['Monster Type']
        monster_exp = int(request.form['EXP'])
        monster_rating = int(request.form['Rating'])
        db_ops.transaction_query([('''
            INSERT INTO monster (monster_name, monster_type, monster_exp, monster_rating)
            VALUES (%s, %s, %s, %s)
        ''', [monster_name, monster_type, monster_exp, monster_rating],)])
        flash('Monster added successfully!')
        return redirect(url_for('view_monsters'))
    return render_template('add_monster.html', logged_in=logged_in)

# Update Monsters
@app.route('/monster/<int:monster_id>/update', methods=['GET', 'POST'])
@login_required
def update_monster(monster_id):
    monster = db_ops.select_query_params('SELECT * FROM monster WHERE monsterID = %s', [monster_id])[0]
    if request.method == 'POST':
        monster_name = request.form['Monster Name']
        monster_type = request.form['Monster Type']
        monster_exp = int(request.form['EXP'])
        monster_rating = int(request.form['Rating'])
        db_ops.transaction_query([('''
            UPDATE monster
            SET monster_name = %s, monster_type = %s, monster_exp = %s, monster_rating = %s
            WHERE monsterID = %s
        ''', [monster_name, monster_type, monster_exp, monster_rating, monster_id],)])
        flash('Monster updated successfully!')
        return redirect(url_for('view_monsters'))
    return render_template('update_monster.html', monster=monster, logged_in=logged_in)

# View NPC
@app.route('/campaign/<int:campaign_id>/<string:campaign_name>/npcs')
@login_required
def view_npcs(campaign_id, campaign_name):
    npcs = db_ops.select_query_params('''
        SELECT * FROM npc WHERE campaignID = %s
    ''', [campaign_id])
    return render_template('view_npcs.html', npcs=npcs, campaign_id=campaign_id, campaign_name=campaign_name, logged_in=logged_in)

# Add NPC
@app.route('/<int:campaign_id>/<string:campaign_name>/npc/add', methods=['GET', 'POST'])
@login_required
def add_npc(campaign_id, campaign_name):
    if request.method == 'POST':
        npc_name = request.form['NPC Name']
        npc_class = request.form['NPC Class']
        npc_affiliation = request.form['Affiliation']
        npc_goal = request.form['Goal']
        alignment = request.form['Alignment']
        affinity = request.form['Party Affinity']
        is_alive = True if 'Is Alive' in request.form else False
        db_ops.transaction_query([('''
            INSERT INTO npc (campaignID, npc_name, npc_class, npc_affiliation, npc_goal, npc_alignment, party_affinity, is_alive)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', [campaign_id, npc_name, npc_class, npc_affiliation, npc_goal, alignment, affinity, is_alive],)])
        flash('NPC added successfully!')
        return redirect(url_for('view_npcs', campaign_id=campaign_id, campaign_name=campaign_name))
    return render_template('add_npc.html', logged_in=logged_in)

# Update NPC
@app.route('/<string:campaign_name>/npc/<int:npc_id>/update', methods=['GET', 'POST'])
@login_required
def update_npc(npc_id, campaign_name):
    npc = db_ops.select_query_params('SELECT * FROM npc WHERE npcID = %s', [npc_id])[0]
    if request.method == 'POST':
        npc_name = request.form['NPC Name']
        npc_class = request.form['NPC Class']
        npc_affiliation = request.form['Affiliation']
        npc_goal = request.form['Goal']
        alignment = request.form['Alignment']
        affinity = request.form['Party Affinity']
        is_alive = True if 'Is Alive' in request.form else False
        db_ops.transaction_query([('''
            UPDATE npc
            SET npc_name = %s, npc_class = %s, npc_affiliation = %s, npc_goal = %s, npc_alignment = %s, party_affinity = %s, is_alive = %s
            WHERE npcID = %s
        ''', [npc_name, npc_class, npc_affiliation, npc_goal, alignment, affinity, is_alive, npc_id],)])
        flash('NPC updated successfully!')
        return redirect(url_for('view_npcs', campaign_id=npc[1], campaign_name=campaign_name, ))
    return render_template('update_npc.html', npc=npc, logged_in=logged_in)

def update_campaign_stats():
    db_ops.select_query(
        '''
            CREATE OR REPLACE VIEW campaign_stats AS
            SELECT 
                dm.dmID,
                campaign.campaignID, 
                campaign.name, 
                COUNT(p.playerID) AS totalPlayers,
                SUM(p.player_gold) + SUM(it.item_cost) AS partyWealth,
                AVG(p.player_level) AS avgLevel,
                AVG(p.player_expTotal) AS avgExp,
                COUNT(E.encounterID) AS totalEncounters, 
                AVG(E.encounter_rating) AS avgDifficulty, 
                COUNT(M.monsterID) AS totalMonsterSpecies, 
                AVG(M.monster_rating) AS avgChallengeRating, 
                COUNT(N.npcID) AS totalNPCs
            FROM campaign
            INNER JOIN dm ON dm.dmID = campaign.dmID 
            INNER JOIN player p ON campaign.campaignID = p.campaignID
            INNER JOIN Inventory i ON p.playerID = i.playerID
            INNER JOIN Items it ON i.itemID = it.itemID
            INNER JOIN Encounter E ON campaign.campaignID = E.campaignID
            INNER JOIN Encounter_Tracker ET ON E.encounterID = ET.encounterID
            INNER JOIN Monster M ON M.monsterID = ET.monsterID
            INNER JOIN NPC N ON campaign.campaignID = N.campaignID
            GROUP BY dm.dmID, campaign.campaignID, campaign.name
            ORDER BY dm.dmID, campaign.campaignID;
        ''')


# Export Campaign   
@app.route('/campaigns/export')
@login_required
def export_campaigns():
    dm_id = session['dm_id']
    update_campaign_stats()
    to_export = db_ops.select_query_params('SELECT * FROM campaign_stats WHERE dmID=%s', [dm_id])

    if not to_export:
        flash("No data found for this campaign or you don't have access.")
        return redirect(url_for('dashboard'))
    
    print(to_export)

    import csv
    keys = ('DM ID', 'Campaign ID', 'Campaign Name', 'Total Players', 'Party Wealth', 'Average Level',
            'Average EXP', 'Total Encounters', 'Average Difficulty', 'Total Monsters Fought', 'Average Challenge Rating')
    data_dicts = [dict(zip(keys, row)) for row in to_export]
    print(keys)
    print(data_dicts)

    csv_filename = 'Campaigns.csv'

    with open(csv_filename, 'w', newline='') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=keys) 
        writer.writeheader() 
        writer.writerows(data_dicts) 

    return send_file(csv_filename, as_attachment=True)
    

if __name__ == '__main__':
    app.run(debug=True)
