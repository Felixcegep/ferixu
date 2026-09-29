"""Maquette NiceGUI : données et actions simulées, sans connexion au matériel."""

import asyncio
import inspect
from datetime import datetime
from nicegui import app, ui

ui.add_css('''
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
body{background:#f7faf6;color:#19352c;font-family:'DM Sans',sans-serif}.nicegui-content{padding:0}
.shell{max-width:1390px;margin:auto;padding:28px 32px 60px}.brand,.title,.hero-title,.value{font-family:Manrope,sans-serif;letter-spacing:-.05em}
.brand{font-size:24px;font-weight:800}.title{font-size:36px;font-weight:800}.hero-title{font-size:31px;font-weight:800}.value{font-size:31px;font-weight:800}
.eyebrow{font-size:11px;font-weight:800;letter-spacing:.16em;color:#6d8578}.muted{color:#6b8175}.tiny{font-size:12px;color:#73867b}
.card{background:white;border:1px solid #e0e9e1;border-radius:20px;padding:22px;box-shadow:0 8px 26px #193c2708}
.hero{border-radius:24px;padding:30px 32px;color:white;min-height:220px}.normal{background:linear-gradient(115deg,#245e44,#3c8662)}.watch{background:linear-gradient(115deg,#9b7330,#c5a354)}.urgent{background:linear-gradient(115deg,#913e38,#c57256)}
.pill{border:1px solid #ffffff44;background:#ffffff22;border-radius:30px;padding:7px 13px;font-weight:700}
.metrics,.charts,.settings{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.charts,.settings{grid-template-columns:repeat(3,minmax(0,1fr))}
.summary{display:grid;grid-template-columns:1.5fr 1fr;gap:16px}.controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.q-btn{text-transform:none;font-weight:700;border-radius:11px}.green-btn{background:#2c7353!important;color:white!important}.outline-btn{border:1px solid #cbdccf;color:#286e50!important}
.q-tab{font-weight:700;text-transform:none;color:#60776a}.q-tab--active{color:#286e50}.q-tab-panel{padding:24px 0 0!important}.q-tab-panels{background:transparent}
.rule{border-bottom:1px solid #e7eee8}.chart-card{min-width:0}.control-card{min-height:205px}.dot{height:10px;width:10px;display:inline-block;border-radius:50%;background:#53a779}.dot.red{background:#d26757}
@media(max-width:1000px){.metrics,.charts{grid-template-columns:repeat(2,minmax(0,1fr))}.summary{grid-template-columns:1fr}}
@media(max-width:650px){.shell{padding:18px 16px 40px}.metrics,.charts,.controls,.settings{grid-template-columns:1fr}.title{font-size:29px}.hero-title{font-size:25px}.hero{padding:24px}}
''', shared=True)


def chart(values, color, unit, minimum=0):
    return {
        'animation': False, 'grid': {'left': 42, 'right': 12, 'top': 16, 'bottom': 30},
        'xAxis': {'type': 'category', 'data': ['06 h', '07 h', '08 h', '09 h', '10 h', '11 h', '12 h', '14 h'], 'boundaryGap': False,
                  'axisLine': {'lineStyle': {'color': '#dce8de'}}, 'axisTick': {'show': False}, 'axisLabel': {'color': '#829186', 'fontSize': 10}},
        'yAxis': {'type': 'value', 'min': minimum, 'splitLine': {'lineStyle': {'color': '#edf2ed'}}, 'axisLabel': {'color': '#829186', 'fontSize': 10}},
        'tooltip': {'trigger': 'axis'},
        'series': [{'type': 'line', 'data': values, 'smooth': True, 'showSymbol': False,
                    'lineStyle': {'color': color, 'width': 3}, 'areaStyle': {'color': color, 'opacity': .12}, 'itemStyle': {'color': color}}],
    }


def metric(name, value, unit, icon, note):
    with ui.column().classes('card w-full gap-3'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label(name).classes('muted font-semibold text-sm')
            ui.icon(icon).classes('text-green-700 text-xl')
        with ui.row().classes('items-baseline gap-1'):
            ui.label(value).classes('value')
            ui.label(unit).classes('muted font-bold')
        ui.label(note).classes('tiny')


def page(active_page: str = 'dashboard', alert: bool = False, watch: bool = False):
    saved = app.storage.user
    state = {'alert': alert, 'watch': watch, 'auto': saved.get('auto', True),
             'count': saved.get('count', 2),
             'last': saved.get('last', f"{datetime.now():%d/%m/%Y} à 09 h 42"),
             'light_test': 'Automatique',
             'humidity': saved.get('humidity', 30),
             'lux': saved.get('lux', 10000),
             'duration': saved.get('duration', 3)}

    def water(name, count_as_watering=True):
        if state['alert']:
            ui.notify('Action refusée : niveau d’eau insuffisant.', type='negative')
            return
        if count_as_watering:
            state['count'] += 1
            state['last'] = f"{datetime.now():%d/%m/%Y à %H h %M}"
            saved['count'] = state['count']
            saved['last'] = state['last']
        ui.notify(f"{name} simulé : pompe activée pendant {state['duration']} seconde(s).", type='positive')
        if active_page == 'dashboard':
            overview.refresh()
        if active_page == 'controls':
            controls.refresh()

    def toggle_auto(value):
        state['auto'] = value
        saved['auto'] = value
        ui.notify('Mode automatique activé.' if value else 'Mode automatique désactivé.', type='positive')
        if active_page == 'dashboard':
            overview.refresh()

    async def test_light():
        client = ui.context.client
        for color in ('Vert', 'Jaune', 'Rouge'):
            state['light_test'] = color
            controls.refresh()
            await asyncio.sleep(.7)
        state['light_test'] = 'Test terminé'
        controls.refresh()
        with client:
            ui.notify('Séquence du feu terminée.', type='positive')

    def save_settings():
        h, lux, duration = humidity_input.value, lux_input.value, duration_input.value
        if any(v is None for v in (h, lux, duration)) or not (1 <= h <= 100 and 1 <= lux <= 100000 and 1 <= duration <= 3):
            ui.notify('Vérifiez les seuils et la durée (1 à 3 secondes).', type='negative')
            return
        state.update(humidity=int(h), lux=int(lux), duration=int(duration))
        saved.update(humidity=state['humidity'], lux=state['lux'], duration=state['duration'])
        ui.notify('Paramètres enregistrés dans la maquette.', type='positive')

    def ask_confirmation(title, description, action):
        with ui.dialog() as dialog, ui.card().classes('card gap-4 min-w-[320px]'):
            ui.label(title).classes('text-xl font-bold')
            ui.label(description).classes('muted')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Annuler', on_click=dialog.close).props('flat color=grey-7')

                async def approve():
                    dialog.close()
                    result = action()
                    if inspect.isawaitable(result):
                        await result

                ui.button('Confirmer', on_click=approve).props('color=green-8')
        dialog.open()

    def request_pump(name, count_as_watering=True):
        if state['alert']:
            ui.notify('Action refusée : niveau d’eau insuffisant.', type='negative')
            return
        ask_confirmation(
            'Confirmer l’arrosage ?' if count_as_watering else 'Confirmer le test de la pompe ?',
            f"La pompe sera activée pendant {state['duration']} seconde(s).",
            lambda: water(name, count_as_watering),
        )

    @ui.refreshable
    def overview():
        alert = state['alert']
        watch = state['watch']
        h, t, lux, light = (24, '22,2', 3100, '2 h 42') if alert else (
            (35, '21,8', 12840, '6 h 24') if watch else (46, '21,8', 12840, '6 h 24')
        )
        with ui.column().classes('w-full gap-4'):
            with ui.column().classes(f'hero w-full justify-between {"urgent" if alert else "watch" if watch else "normal"}'):
                with ui.row().classes('w-full justify-between items-start gap-3'):
                    with ui.column().classes('gap-2'):
                        ui.label('ÉTAT DE LA PLANTE').classes('eyebrow !text-white')
                        ui.label('Intervention nécessaire' if alert else 'Plante à surveiller' if watch else 'Votre plante se porte bien').classes('hero-title')
                        ui.label('Réservoir vide et sol trop sec. Remplissez le réservoir pour permettre un arrosage.' if alert else 'Humidité du sol entre 30 % et 39 %. Surveillez son évolution.' if watch else 'Humidité, lumière et réserve d’eau sont dans les plages attendues.').classes('text-white/90')
                    ui.label('●  URGENT' if alert else '●  À SURVEILLER' if watch else '●  NORMAL').classes('pill')
                ui.label('Dernière lecture simulée · aujourd’hui à 14 h 30 · fréquence prévue : 10 min').classes('text-xs text-white/80')
            with ui.element('div').classes('metrics w-full'):
                metric('Humidité du sol', str(h), '%', 'water_drop', f"Arrosage sous {state['humidity']} %")
                metric('Température du sol', t, '°C', 'thermostat', 'Lecture toutes les 10 min')
                metric('Luminosité', f'{lux:,}'.replace(',', ' '), 'lux', 'wb_sunny', f"Lumière suffisante dès {state['lux']:,} lux".replace(',', ' '))
                metric('Lumière reçue', light, '', 'light_mode', 'Objectif quotidien : 6 à 8 h')
            with ui.element('div').classes('summary w-full'):
                with ui.column().classes('card gap-4'):
                    ui.label('Aujourd’hui, en un coup d’œil').classes('text-lg font-bold')
                    for label, value in [('Réservoir', 'Insuffisant' if alert else 'Suffisant'),
                                         ('Feu tricolore', '🔴 Rouge · urgent' if alert else '🟡 Jaune · à surveiller' if watch else '🟢 Vert · normal'),
                                         ('Mode automatique', 'Activé' if state['auto'] else 'Désactivé')]:
                        with ui.row().classes('w-full justify-between items-center rule pb-3'):
                            ui.label(label).classes('muted')
                            ui.label(value).classes('font-bold')
                with ui.column().classes('card gap-2'):
                    ui.label('Arrosage').classes('text-lg font-bold')
                    ui.label(state['last']).classes('font-bold text-lg')
                    ui.label('Dernier arrosage').classes('tiny')
                    ui.separator()
                    ui.label(f"{state['count']} / 6 arrosages sur 24 h").classes('font-bold text-lg')
                    ui.label('Délai minimal entre arrosages automatiques : 30 min.').classes('tiny')
            ui.label('Évolution des mesures').classes('text-xl font-bold mt-3')
            plots = [
                ('Humidité du sol', '%', [44,40,36,32,29,27,25,24] if alert else [42,41,39,38,37,36,35,35] if watch else [52,50,48,45,42,46,45,46], '#348d67', 0),
                ('Luminosité', 'lux', [400,1800,4400,6700,5200,4500,3600,3100] if alert else [900,3400,9200,13200,14800,13500,12400,12840], '#d4a34c', 0),
                ('Température du sol', '°C', [20.2,20.8,21.5,22.1,22.6,22.5,22.3,22.2] if alert else [19.7,20.1,20.8,21.4,22,22.1,21.9,21.8], '#7593a4', 18),
            ]
            with ui.element('div').classes('charts w-full'):
                for title, unit, values, color, minimum in plots:
                    with ui.column().classes('card chart-card gap-1'):
                        ui.label(title).classes('font-bold')
                        ui.label(f'Évolution sur la journée · {unit}').classes('tiny')
                        ui.echart(chart(values, color, unit, minimum)).classes('w-full h-44')

    @ui.refreshable
    def controls():
        with ui.column().classes('w-full gap-5'):
            ui.label('Contrôles manuels').classes('title')
            ui.label('Actions simulées : aucun matériel n’est activé.').classes('muted')
            with ui.row().classes('items-center gap-2'):
                ui.label('Réservoir simulé :').classes('muted')
                ui.button('Suffisant', on_click=lambda: ui.navigate.to('/controles')).props('outline color=green-8')
                ui.button('Insuffisant', on_click=lambda: ui.navigate.to('/controles?reservoir=vide')).props('outline color=red-7')
            if state['alert']:
                with ui.row().classes('card w-full items-center gap-3 !bg-red-50'):
                    ui.icon('warning_amber').classes('text-red-600 text-2xl')
                    ui.label('Réservoir insuffisant : la pompe reste bloquée en mode manuel et automatique.').classes('text-red-800 font-semibold')
            with ui.element('div').classes('controls w-full'):
                entries = [
                    ('water_drop', 'Arroser maintenant', f"Arrosage manuel de {state['duration']} seconde(s), si le réservoir contient de l’eau.", 'Arroser maintenant', lambda: request_pump('Arrosage manuel')),
                    ('precision_manufacturing', 'Tester le relais et la pompe', 'Test de 3 secondes maximum, refusé si le réservoir est vide.', 'Lancer le test', lambda: request_pump('Test de la pompe', count_as_watering=False)),
                    ('traffic', 'Tester le feu tricolore', f"Séquence vert → jaune → rouge · état : {state['light_test']}", 'Lancer le test', lambda: ask_confirmation('Confirmer le test du feu ?', 'Le feu affichera successivement vert, jaune et rouge.', test_light)),
                ]
                for icon, title, description, button, action in entries:
                    with ui.column().classes('card control-card gap-3'):
                        light_color = {'Jaune': 'text-yellow-600', 'Rouge': 'text-red-600'}
                        icon_color = light_color.get(state['light_test'], 'text-green-700') if icon == 'traffic' else 'text-green-700'
                        ui.icon(icon).classes(f'{icon_color} text-3xl')
                        ui.label(title).classes('text-lg font-bold')
                        ui.label(description).classes('muted')
                        ui.button(button, on_click=action).props('color=green-8').classes('green-btn mt-auto')
                with ui.column().classes('card control-card gap-3'):
                    ui.icon('autorenew').classes('text-green-700 text-3xl')
                    ui.label('Arrosage automatique').classes('text-lg font-bold')
                    ui.label(f"Sol < {state['humidity']} % : pompe {state['duration']} s; pause 30 min; maximum 6 fois/24 h.").classes('muted')
                    ui.switch('Mode automatique', value=state['auto'], on_change=lambda e: toggle_auto(e.value)).classes('mt-auto')

    with ui.column().classes('shell w-full gap-0'):
        with ui.row().classes('w-full justify-between items-center pb-7'):
            ui.label('✿ Pousse').classes('brand')
            ui.label('●  MAQUETTE · DONNÉES SIMULÉES').classes('eyebrow')
        with ui.row().classes('w-full justify-between items-end gap-4 pb-5'):
            with ui.column().classes('gap-1'):
                ui.label('TABLEAU DE BORD').classes('eyebrow')
                ui.label('Ma plante en pot').classes('title')
                ui.label('Surveillance et arrosage intelligents').classes('muted')
        with ui.row().classes('w-full gap-2 border-b border-green-100 pb-3'):
            destinations = [
                ('État normal', '/'), ('À surveiller', '/surveillance'), ('État d’alerte', '/alerte'),
                ('Contrôles', '/controles'), ('Paramètres', '/parametres'),
            ]
            current = ('/alerte' if alert else '/surveillance' if watch else '/') if active_page == 'dashboard' else {
                'controls': '/controles', 'settings': '/parametres',
            }[active_page]
            for label, destination in destinations:
                selected = destination == current
                ui.button(label, on_click=lambda target=destination: ui.navigate.to(target)).props(
                    'unelevated color=green-8' if selected else 'flat color=grey-7'
                )
        if active_page == 'dashboard':
            overview()
        elif active_page == 'controls':
            controls()
        else:
            with ui.column().classes('w-full gap-5'):
                ui.label('Paramètres du système').classes('title')
                ui.label('Modifiez les seuils affichés dans cette maquette.').classes('muted')
                with ui.element('div').classes('settings w-full'):
                    with ui.column().classes('card gap-3'):
                        ui.icon('water_drop').classes('text-green-700 text-3xl')
                        ui.label('Humidité minimale').classes('text-lg font-bold')
                        ui.label('Arrosage automatique sous ce seuil.').classes('muted')
                        humidity_input = ui.number('Seuil (%)', value=state['humidity'], min=1, max=100, step=1).classes('w-full')
                    with ui.column().classes('card gap-3'):
                        ui.icon('wb_sunny').classes('text-green-700 text-3xl')
                        ui.label('Lumière suffisante').classes('text-lg font-bold')
                        ui.label('Cumul des heures au-dessus du seuil.').classes('muted')
                        lux_input = ui.number('Seuil (lux)', value=state['lux'], min=1, max=100000, step=100).classes('w-full')
                    with ui.column().classes('card gap-3'):
                        ui.icon('timer').classes('text-green-700 text-3xl')
                        ui.label('Durée d’arrosage').classes('text-lg font-bold')
                        ui.label('Maximum de sécurité : 3 secondes.').classes('muted')
                        duration_input = ui.number('Durée (secondes)', value=state['duration'], min=1, max=3, step=1).classes('w-full')
                ui.button('Enregistrer les paramètres', icon='save', on_click=save_settings).props('color=green-8').classes('green-btn self-start')
                with ui.column().classes('card w-full gap-2'):
                    ui.label('Règles du feu tricolore').classes('text-lg font-bold')
                    ui.label('🟢 Vert : humidité ≥ 40 %, lumière ≥ 6 h, réservoir suffisant.')
                    ui.label('🟡 Jaune : humidité de 30 à 39 % ou lumière < 4,8 h.')
                    ui.label('🔴 Rouge prioritaire : humidité < 30 %, lumière < 3,6 h ou réservoir insuffisant.')
                    ui.label('Retour à la couleur correspondante à la prochaine lecture, toutes les 10 minutes.').classes('tiny')


@ui.page('/')
def normal_page():
    page('dashboard')


@ui.page('/alerte')
def alert_page():
    page('dashboard', alert=True)


@ui.page('/surveillance')
def watch_page():
    page('dashboard', watch=True)


@ui.page('/controles')
def controls_page(reservoir: str = 'suffisant'):
    page('controls', alert=reservoir == 'vide')


@ui.page('/parametres')
def settings_page():
    page('settings')


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='Pousse · Maquette d’irrigation', port=8080, reload=False,
           storage_secret='pousse-maquette-locale', show_welcome_message=False)
