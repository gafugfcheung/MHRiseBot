import os
import string

import discord
import nltk
from dotenv import load_dotenv
from xml.dom import minidom

load_dotenv()
TOKEN = os.getenv("token")
client = discord.Client()
servers = [875595883276795935]


def clean_name(text):
    return text.translate(str.maketrans('', '', string.punctuation)).lower().replace(" ", "")


def grade_to_skill(items):
    return [f"Any {r} Grade Skill" for r in items]


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message):
    if message.author == client.user or not message.content.startswith("$"):
        return

    # if message.guild.id not in servers:
    #     return

    if message.guild.id == 875595883276795935 and message.channel.id != 910564440917827594:
        await message.channel.send("Please use the <#910564440917827594> channel for bot commands.")
        return

    embed_color = 0x00ff00
    user_input = message.content.lower()

    if user_input.startswith("$monster"):
        monster_closest_dist = 1000
        monster_closest_names = set()
        input_monster_name = clean_name(user_input[8:])

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
                    monster_embed = discord.Embed(title=f"**Monster: {monster_name}**", description=wiki, color=embed_color)
                    monster_embed.set_thumbnail(url=f"attachment://{thumbnail_path}")
                    monster_embed.add_field(name="**Monster Class:**", value=monster_class, inline=False)
                    monster_embed.add_field(name="**Weakness(es):**", value=weakness)
                    monster_embed.add_field(name="**Element(s):**", value=element)
                    monster_embed.add_field(name="**Ailment(s):**", value=ailment)
                    monster_embed.add_field(name="**Characteristics:**", value=f"*{characteristics}*")

                    monster_files = [monster_thumbnail]
                    # hzv_path = f"{name.lower()}_hzv.png"
                    # full_hzv_path = f"images/{hzv_path}"
                    # if os.path.exists(full_hzv_path):
                    #     hzv = discord.File(full_hzv_path, filename=hzv_path)
                    #     embed.set_image(url=f"attachment://{hzv_path}")
                    #     files.append(hzv)

                    await message.channel.send(files=monster_files, embed=monster_embed)
                    return

                if distance < 4 and distance < monster_closest_dist:
                    monster_closest_dist = distance
                    monster_closest_names.add(monster_name)

        monster_warning = f"Could not find monster: `{input_monster_name}`. "
        if len(monster_closest_names) > 0:
            monster_warning = f"{monster_warning}Perhaps you mean: {', '.join([f'`{n}`' for n in list(monster_closest_names)])}?"

        await message.channel.send(monster_warning)
        return

    elif user_input.startswith("$skill"):
        skill_closest_dist = 1000
        skill_closest_names = set()
        input_skill_name = clean_name(user_input[6:])

        for skill in minidom.parse("assets/skills.xml").getElementsByTagName("skill"):
            skill_name = skill.attributes["name"].value
            cleaned_skill_name = clean_name(skill_name)
            distance = nltk.edit_distance(input_skill_name, cleaned_skill_name)

            if distance == 0:
                description = skill.attributes["description"].value
                levels = skill.attributes["levels"].value
                effects = skill.attributes["effects"].value

                skill_embed = discord.Embed(title=f"**Armor Skill: {skill_name}**", description=description, color=embed_color)
                skill_embed.add_field(name="**Level:**", value=levels)
                skill_embed.add_field(name="**Effect by Level:**", value=effects)

                try:
                    grade = skill.attributes["grade"].value
                    firstmaxlevel = skill.attributes["firstmaxlevel"].value
                    secondmaxlevel = skill.attributes["secondmaxlevel"].value
                    maxslots = skill.attributes["maxslots"].value

                    skill_embed.add_field(name="\u200b", value="\u200b", inline=False)
                    skill_embed.add_field(name="**Skill Grade:**", value=grade)
                    skill_embed.add_field(name="**1st Skill Max Lv:**", value=firstmaxlevel)
                    skill_embed.add_field(name="**2nd Skill Max Lv:**", value=secondmaxlevel)

                    standard_rows = ["S", "A", "B", "C"]
                    minus_rows = standard_rows.copy()
                    minus_rows.remove(grade)
                    first_skill_grade = "\n".join([skill_name] * 5 + grade_to_skill(minus_rows))
                    second_skill_grade = "\n".join(grade_to_skill(standard_rows) + ["(None)"] + [skill_name] * 3)

                    skill_embed.add_field(name="\u200b", value="\u200b", inline=False)
                    skill_embed.add_field(name="**1st Skill**", value=first_skill_grade)
                    skill_embed.add_field(name="**2nd Skill**", value=second_skill_grade)
                    skill_embed.add_field(name="**Max Slot**", value=maxslots)

                except KeyError:
                    pass

                await message.channel.send(embed=skill_embed)
                return

            if distance < 6 and distance < skill_closest_dist:
                skill_closest_dist = distance
                skill_closest_names.add(skill_name)

        monster_warning = f"Could not find skill: `{input_skill_name}`. "
        if len(skill_closest_names) > 0:
            monster_warning = f"{monster_warning}Perhaps you mean: {', '.join([f'`{n}`' for n in list(skill_closest_names)])}?"

        await message.channel.send(monster_warning)
        return

    else:
        monster_embed = discord.Embed(title=f"**Master Utsushi**", description="MH Rise Bot", color=embed_color)
        monster_embed.add_field(name="**Command**", value="$monster [monster name]\n$skill [skill name]")
        monster_embed.add_field(name="**Description**", value="Get info for a specific monster.\nGet info for a specific armor skill.")
        await message.channel.send(embed=monster_embed)
        return



client.run(TOKEN)
