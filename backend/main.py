import random
import asyncio
import time
import numpy as np
import json
from fastapi import FastAPI, WebSocket
import uvicorn
import threading

# Створюємо FastAPI
app = FastAPI()

WORLD_SIZE = 10

Personalities = ["agressor", "victim", "rescuer"]
Names = [
    "Liam", "Emma", "Noah", "Olivia", "William", "Ava", "James", "Isabella", "Oliver", "Sophia",
    "Benjamin", "Charlotte", "Elijah", "Mia", "Lucas", "Amelia", "Mason", "Harper", "Logan", "Evelyn",
    "Alexander", "Abigail", "Ethan", "Ella", "Jacob", "Scarlett", "Michael", "Grace", "Daniel", "Chloe",
    "Henry", "Lily", "Jackson", "Aria", "Sebastian", "Zoe", "Aiden", "Penelope", "Matthew", "Layla",
    "Samuel", "Riley", "David", "Nora", "Joseph", "Hazel", "Carter", "Victoria", "Owen", "Hannah"
]
Skills = ["Intelligence", "Strength", "Social", "Crafting"]

main_log = []

def logf(text):
    print(text)
    main_log.append(text)


class Food:
    def __init__(self):
        self.x = random.randint(0, WORLD_SIZE - 1)
        self.y = random.randint(0, WORLD_SIZE - 1)
        self.nutrition = random.randint(10, 30)

# Клас предметів для навчання
class Item:
    def __init__(self, name, skill):
        self.name = name
        self.skill = skill
    def use(self, char):
        self.skill(char)
class TrainingItem(Item):
    def __learn_template(self, char):
        if self.learnskill in char.skills:
            char.skills[self.learnskill] += random.randrange(3,15)
        else:
            char.skills.update({self.learnskill: random.randrange(3,15)})
    def __init__(self, name, skill):
        super().__init__(name, self.__learn_template)
        self.learnskill = skill
        self.x = random.randint(0, WORLD_SIZE - 1)
        self.y = random.randint(0, WORLD_SIZE - 1)
    def use(self, char):
        return super().use(char)


training_items = [
    TrainingItem("Book", "Intelligence"),
    TrainingItem("Gym", "Strength"),
    TrainingItem("Workshop", "Crafting")
]


class Skill:
    def __init__(self, name, ability):
        self.name = name
        self.ability = ability

class Entity: #Base entity doesnt have memory or energy, have health and skills
    skills = {}

    def __init__(self, world, name, age, skills): #name, age, skills[list]
        self.name = name
        self.age = age
        self.skills = skills
        self.health = random.randrange(90, 110)
        self.alive = True
        self.x = random.randint(0, WORLD_SIZE - 1)
        self.y = random.randint(0, WORLD_SIZE - 1)
    def update_health(self, change): #update healt original hp + (change)
        self.health =  self.health + change
    def add_skill(self, skill: Skill, level: int): #Add skill with level {skill: level}
        self.skills.update({skill: level})
   
            

class Character(Entity):
    child = []
    def move(self):
        """Переміщення по карті"""
        dx, dy = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
        self.x = max(0, min(WORLD_SIZE - 1, self.x + dx))
        self.y = max(0, min(WORLD_SIZE - 1, self.y + dy))
        logf(f"🚶 {self.name} moved to ({self.x}, {self.y})")

    def reproduction(self, man, women):
        if len(man.child) <= 3 or len(women.child) <= 3: 
            gains_skills = {**man.skills, **women.skills}
            print(list(gains_skills.keys()))
            new_skill = random.choice(list(gains_skills.keys()))
            skill = dict()
            try:
                skill = {new_skill : man.skills[new_skill] if women.skills[new_skill] == man.skills[new_skill] else random.randrange(man.skills[new_skill], women.skills[new_skill])}
            except:
                skill = {new_skill: random.randrange(5,10)}
            baby = NPC(self.world, None, 0, skill)
            man.child.append(baby)
            women.child.append(baby)
            self.world.add_character(baby)
            logf(f"👶 {man.name} and {women.name} gave birth named {baby.name} with gain {list(baby.skills.keys())[0]}")

    def sleep(self):
        """Отдих шоб востановить енергію"""
        if self.energy < 100:
            change = random.randrange(30,60)
            self.energy += change
            logf(f"😴 {self.name} Sleeped and recover {change} energy.")

    def train(self):
        """Тренування навички"""
        skill = random.choice(list(self.skills.keys()))
        self.skills[skill] += 1 if self.age > 40 else random.randrange(2,5)
        logf(f"💪 {self.name} improved {skill}. New level: {self.skills[skill]}")

    def use_item(self):
        """Тренування через предмети"""
        nearby_items = [item for item in training_items if abs(item.x - self.x) <= 1 and abs(item.y - self.y) <= 1]
        
        if not nearby_items:
            return
        
        item = random.choice(nearby_items)
        item.skill()
        logf(f"📖 {self.name} trained at {item.name}. {item.learnskill} is now {self.skills[item.learnskill]}")


    def interact(self):
        """Взаємодія з іншим персонажем"""
        nearby_characters = [
            char for char in self.world.characters
            if char != self and char.alive and abs(char.x - self.x) <= 1 and abs(char.y - self.y) <= 1
        ]

        if not nearby_characters:
            return
        
        other = random.choice(nearby_characters)
        if other == self or not other.alive:
            return

        if other.name not in self.relationships:
            self.relationships[other.name] = 0
        
        if self.relationships[other.name] >= 30:
            if random.choice([True, False]) == True:
                self.reproduction(self, other)
        
        change = random.randint(-5, 10)
        if "Social" in self.skills:
            change = random.randint(-5+self.skills["Social"], 3*self.skills["Social"])
        self.relationships[other.name] += change
        logf(f"🤝 {self.name} interacted with {other.name}. Relationship: {self.relationships[other.name]}")
        if change > 0:
            try:
                self.skills["Social"] += random.randrange(1, 3)
            except KeyError:
                self.skills.update({"Social": random.randrange(1, 3)})
        logf(f"💪 {self.name} improved Social by Interact. New level: {self.skills["Social"]}")

    def die(self):
        """Персонаж помирає"""
        self.alive = False
        logf(f"💀 {self.name} has died at age {self.age}.")
        self.world.characters.remove(self)

    def eat(self):
        """Знайти та з'їсти їжу"""
        nearby_food = self.world.get_nearby_food(self)
        if nearby_food:
            food = random.choice(nearby_food)
            self.hunger -= food.nutrition
            logf(f"🍏 {self.name} eated food with {food.nutrition} nutrutition.")
            self.world.food.remove(food)

    def age_up(self):
        """Старіння та зниження енергії"""
        self.age += 1
        self.energy -= random.randint(5, 15)
        logf(f"📆 {self.name} is now {self.age} years old. Energy: {self.energy}. Hunger: {self.hunger}")
        if self.energy <= 0:
            self.die()

    actions = [age_up, interact, train, sleep, move, eat]
    
    async def live(self):
        #main live cycle of character
        #await asyncio.sleep(random.uniform(1,3)) # simulation of life
        self.hunger += random.randint(5, 10)
        if self.hunger >= 80:
            self.eat()
        if self.hunger >= 30:
            self.interact()
        if self.hunger >= 100:
            self.die()
            return
        self.move()
        await random.choice(self.actions)(self)

    def __init__(self, world, name, age, skills, personality):
        super().__init__(world, name, age, skills)
        self.world = world
        self.memory = []
        self.personality = personality
        self.energy = 100
        self.hunger = random.randint(0, 30)
        self.relationships = {} # {character_id: "рівень дружби"}
    def update_energy(self, change):
        self.energy = max(0, min(100, self.energy + change))


class NPC(Character):
    def __init__(self, world, name=None, age=None, skills=None, personality=None):
        randskills = {}
        for skill in Skills:
            randskills.update({skill: random.randint(1, 10)})
        super().__init__(
            world, 
            name if name != None else random.choice(Names), 
            age if age != None else random.randint(10,50), 
            skills if skills != None else randskills, 
            personality if personality != None else random.choice(Personalities)
            )

class World:
    def __init__(self, num_characters=10):
        self.characters = [NPC(self) for _ in range(num_characters)]
        self.food = [Food() for _ in range(100)]
        self.core_chars = []
        self.tasks = []
        self.lock = asyncio.Lock()
    def get_world_state(self):
        """Отримати стан світу"""
        return {
            "characters": [
                {"name": char.name, "x": char.x, "y": char.y, "age": char.age, "energy": char.energy, "hunger": char.hunger, "alive": char.alive}
                for char in self.characters
            ],
            "food": [{"x": food.x, "y": food.y, "nutrition": food.nutrition} for food in self.food],
            "log": main_log[-10:]
        }
    def get_nearby_food(self, character):
        """Отримати їжу поруч"""
        return [food for food in self.food if abs(food.x - character.x) <= 2 and abs(food.y - character.y) <= 2]
    def lived(self) -> int:
        return len(self.characters)
    async def runcycle(self):
        pass
    async def run(self):
        """Запуск гри, де всі персонажі існують одночасно"""
        """self.q = asyncio.Queue()
        def diff(l1, l2):
            return list(set(l2) - set(l1))
        self.core_chars = diff(self.core_chars, self.characters)
        print(self.core_chars)"""
        logf(f"🌎 {self.lived()} now live on planet")
        time.sleep(3)
        #self.runcycle()
        while True:
            async with self.lock:
                for char in self.characters:
                    asyncio.create_task(char.live())
                    await asyncio.sleep(0.1)
        #await asyncio.gather(*self.tasks)

    async def kostulb(self):
        while self.lived() <= 0:
            if self.lived() > 0:
                await asyncio.sleep(2)

    def add_character(self, character):
        """Додає нового персонажа і запускає його"""
        self.characters.append(character)
        #task = asyncio.create_task(character.live())
        #self.tasks.append(task)


world = World(num_characters=10)

@app.get("/world")
async def get_world():
    """Отримати стан світу через REST API"""
    return world.get_world_state()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Підключення WebSocket для спостереження за світом"""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(world.get_world_state())
            await asyncio.sleep(1)
    except:
        pass  # Якщо клієнт відключається, не зупиняємо сервер

# Асинхронний запуск сервера
def start_game():
    """Запускає гру у фоновому режимі"""
    asyncio.run(world.run())  # Запускаємо симуляцію

if __name__ == "__main__":
    threading.Thread(target=start_game).start()  # Запускаємо гру перед сервером
    uvicorn.run(app, host="0.0.0.0", port=8000)