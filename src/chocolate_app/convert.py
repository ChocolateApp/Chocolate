import os, subprocess

# Définissez le chemin du dossier contenant les fichiers vidéos à réduire
# par exemple :
# folder_path = "C:\\Videos\\"
folder_path = r"E:\\Séries\\The Mentalist"

# Itérez sur tous les dossiers dans le dossier
allSeasons = [
    f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))
]
for seasons in allSeasons:
    allEpisodes = [
        f
        for f in os.listdir(os.path.join(folder_path, seasons))
        if os.path.isfile(os.path.join(folder_path, seasons, f))
    ]
    for filename in allEpisodes:
        # Vérifiez que le fichier est une vidéo en utilisant son extension de fichier
        if (
            filename.endswith(".mp4")
            or filename.endswith(".mkv")
            or filename.endswith(".avi")
        ):
            # Construisez le chemin complet du fichier vidéo en utilisant le chemin du dossier et le nom de fichier
            filepath = f"{folder_path}\\{seasons}\\{filename}"
            newFilepath, file_extension = os.path.splitext(filepath)
            newFilepath += f"_compressed.{file_extension}"

            # Utilisez ffmpeg pour réduire la taille du fichier vidéo en utilisant un taux de bits constant
            command = [
                "ffmpeg",
                "-i",
                filepath,
                "-c",
                "copy",
                "-c:v",
                "h264_nvenc",
                "-qp",
                "0",
                "-c:a",
                "copy",
                "-y",
                "-vsync",
                "0",
                "-crf",
                "22",
                "-pix_fmt",
                "yuv420p",
                "-b:v",
                "5M",
                f"{newFilepath}",
            ]

            subprocess.run(command)
