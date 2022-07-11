import os
import string
from dataclasses import dataclass
from xml.dom import minidom

import discord
import nltk
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("token")
client = discord.Client()

MIN_CLOSEST_DISTANCE = 1000
EMBED_COLOR = 0x00ff00


@dataclass
class Command:
    command: str
    usage: str
    description: str

    def get_header(self):
        return f"{COMMAND_HEADER}{self.command} "


command_get_monster = Command("monster", "monster [monster name]", "Get info for a specific monster.")
command_get_skill = Command("skill", "skill [skill name]", "Get info for a specific skill.")
COMMAND_HEADER = "$"
COMMANDS = [
    command_get_monster,
    command_get_skill
]


ENABLED_SERVERS = [
    875595883276795935,  # Monster Hunter Corps
    909657426037469184,  # Test Server
]
ENABLED_CHANNELS = [
    910564440917827594,  # scrolls-of-monsters
    909657426037469187,  # Test Server general
]


def clean_name(text):
    return text.translate(str.maketrans('', '', string.punctuation)).lower().replace(" ", "")


def grade_to_skill(items):
    return [f"Any {r} Grade Skill" for r in items]


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message):
    if (
        message.author == client.user
        or not message.content.startswith(COMMAND_HEADER)
        or message.guild is None
        or message.channel is None
    ):
        return

    if message.guild.id not in ENABLED_SERVERS and message.channel.id not in ENABLED_CHANNELS:
        # await message.channel.send("Please use the <#910564440917827594> channel for bot commands.")
        return

    user_input = message.content.lower()

    if user_input.startswith(command_get_monster.get_header()):
        monster_closest_dist = MIN_CLOSEST_DISTANCE
        monster_closest_names = set()

        header_length = len(command_get_monster.get_header())
        user_input_monster = user_input[header_length:]
        input_monster_name = clean_name(user_input_monster)

        for monster in minidom.parse("assets/monsters.xml").getElementsByTagName("monster"):
            monster_name = monster.attributes["name"].value
            cleaned_monster_names = [clean_name(monster_name)]
            try:
                monster_alias = monster.attributes["alias"].value
                cleaned_monster_names.extend([clean_name(a) for a in monster_alias.split(",")])
            except KeyError:
                pass

            for cleaned_name in cleaned_monster_names:
                distance = nltk.edit_distance(input_monster_name, cleaned_name)

                if distance == 0:
                    thumbnail_path = f"{monster_name.lower().replace(' ', '_')}.png"
                    wiki = monster.attributes["wiki"].value
                    monster_class = monster.attributes["class"].value
                    weakness = monster.attributes["weakness"].value
                    element = monster.attributes["element"].value
                    ailment = monster.attributes["ailment"].value
                    characteristics = monster.attributes["characteristics"].value

                    monster_thumbnail = discord.File(f"images/{thumbnail_path}", filename=thumbnail_path)
                    monster_embed = discord.Embed(
                        title=f"**Monster: {monster_name}**", description=wiki, color=EMBED_COLOR
                    )
                    monster_embed.set_thumbnail(url=f"attachment://{thumbnail_path}")
                    monster_embed.add_field(name="**Monster Class:**", value=monster_class, inline=False)
                    monster_embed.add_field(name="**Weakness(es):**", value=weakness)
                    monster_embed.add_field(name="**Element(s):**", value=element)
                    monster_embed.add_field(name="**Ailment(s):**", value=ailment)
                    monster_embed.add_field(name="**Characteristics:**", value=f"*{characteristics}*")

                    monster_files = [monster_thumbnail]
                    hzv_path = f"{monster_name.lower()}_hzv.png"
                    full_hzv_path = f"images/{hzv_path}"
                    if os.path.exists(full_hzv_path):
                        hzv = discord.File(full_hzv_path, filename=hzv_path)
                        monster_embed.set_image(url=f"attachment://{hzv_path}")
                        monster_files.append(hzv)

                    await message.channel.send(files=monster_files, embed=monster_embed)
                    return

                if distance < 4 and distance < monster_closest_dist:
                    monster_closest_dist = distance
                    monster_closest_names.add(monster_name)

        monster_warning = f"Could not find monster: `{user_input_monster}`. "
        if len(monster_closest_names) > 0:
            monster_warning = f"""
                {monster_warning}Perhaps you mean: {', '.join([f'`{n}`' for n in list(monster_closest_names)])}?
            """

        await message.channel.send(monster_warning)
        return

    elif user_input.startswith(command_get_skill.get_header()):
        skill_closest_dist = MIN_CLOSEST_DISTANCE
        skill_closest_names = set()

        header_length = len(command_get_skill.get_header())
        user_input_skill = user_input[header_length:]
        input_skill_name = clean_name(user_input_skill)

        for skill in minidom.parse("assets/skills.xml").getElementsByTagName("skill"):
            skill_name = skill.attributes["name"].value
            cleaned_skill_name = clean_name(skill_name)
            distance = nltk.edit_distance(input_skill_name, cleaned_skill_name)

            if distance == 0:
                description = skill.attributes["description"].value
                levels = skill.attributes["levels"].value
                effects = skill.attributes["effects"].value

                skill_embed = discord.Embed(
                    title=f"**Armor Skill: {skill_name}**", description=description, color=EMBED_COLOR
                )
                skill_embed.add_field(name="**Level:**", value=levels)
                skill_embed.add_field(name="**Effect by Level:**", value=effects)

                try:
                    grade = skill.attributes["grade"].value
                    first_max_level = skill.attributes["firstmaxlevel"].value
                    second_max_level = skill.attributes["secondmaxlevel"].value
                    max_slots = skill.attributes["maxslots"].value

                    skill_embed.add_field(name="\u200b", value="\u200b", inline=False)
                    skill_embed.add_field(name="**Skill Grade:**", value=grade)
                    skill_embed.add_field(name="**1st Skill Max Lv:**", value=first_max_level)
                    skill_embed.add_field(name="**2nd Skill Max Lv:**", value=second_max_level)

                    standard_rows = ["S", "A", "B", "C"]
                    minus_rows = standard_rows.copy()
                    minus_rows.remove(grade)
                    first_skill_grade = "\n".join([skill_name] * 5 + grade_to_skill(minus_rows))
                    second_skill_grade = "\n".join(grade_to_skill(standard_rows) + ["(None)"] + [skill_name] * 3)

                    skill_embed.add_field(name="\u200b", value="\u200b", inline=False)
                    skill_embed.add_field(name="**1st Skill**", value=first_skill_grade)
                    skill_embed.add_field(name="**2nd Skill**", value=second_skill_grade)
                    skill_embed.add_field(name="**Max Slot (no lv4 slot)**", value=max_slots)

                except KeyError:
                    pass

                await message.channel.send(embed=skill_embed)
                return

            if distance < 6 and distance < skill_closest_dist:
                skill_closest_dist = distance
                skill_closest_names.add(skill_name)

        monster_warning = f"Could not find skill: `{user_input_skill}`. "
        if len(skill_closest_names) > 0:
            monster_warning = f"""
                {monster_warning}Perhaps you mean: {', '.join([f'`{n}`' for n in list(skill_closest_names)])}?
            """

        await message.channel.send(monster_warning)
        return

    else:
        command_usage_fields = "\n".join([f"{COMMAND_HEADER}{c.usage}" for c in COMMANDS])
        command_description_fields = "\n".join([c.description for c in COMMANDS])

        monster_embed = discord.Embed(title=f"**Master Utsushi**", description="MH Rise Bot", color=EMBED_COLOR)
        monster_embed.add_field(name="**Command**", value=command_usage_fields)
        monster_embed.add_field(name="**Description**", value=command_description_fields)
        await message.channel.send(embed=monster_embed)
        return


client.run(TOKEN)
