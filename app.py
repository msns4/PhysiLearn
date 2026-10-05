import customtkinter as ctk
import subprocess
import sys
# ---------------- App setup ----------------

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("PhysiLearn")
app.geometry("1000x650")
app.minsize(900, 600)


# ---------------- Helpers ----------------

def clear_screen():
    """Remove everything currently displayed."""
    for widget in app.winfo_children():
        widget.destroy()


# ---------------- HOME SCREEN ----------------

def show_home():
    clear_screen()

    main_frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )
    main_frame.pack(fill="both", expand=True)

    # Logo
    logo = ctk.CTkLabel(
        main_frame,
        text="PhysiLearn",
        font=ctk.CTkFont(
            size=42,
            weight="bold"
        )
    )
    logo.pack(pady=(70, 5))

    subtitle = ctk.CTkLabel(
        main_frame,
        text="Learn through movement.",
        font=ctk.CTkFont(size=20)
    )
    subtitle.pack(pady=(0, 45))

    # ASL card
    asl_card = ctk.CTkFrame(
        main_frame,
        width=600,
        height=300,
        corner_radius=25
    )
    asl_card.pack(pady=10)
    asl_card.pack_propagate(False)

    asl_title = ctk.CTkLabel(
        asl_card,
        text="ASL Learning",
        font=ctk.CTkFont(
            size=30,
            weight="bold"
        )
    )
    asl_title.pack(pady=(40, 10))

    asl_description = ctk.CTkLabel(
        asl_card,
        text=(
            "Practice ASL fingerspelling using your camera.\n"
            "Get real-time feedback as you learn."
        ),
        font=ctk.CTkFont(size=17),
        justify="center"
    )
    asl_description.pack(pady=10)

    start_button = ctk.CTkButton(
        asl_card,
        text="Start ASL Lesson",
        command=show_lesson,
        width=260,
        height=55,
        corner_radius=15,
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        )
    )
    start_button.pack(pady=30)

    footer = ctk.CTkLabel(
        main_frame,
        text=(
            "Computer Vision  •  Interactive Learning  •  "
            "Real-Time Feedback"
        ),
        font=ctk.CTkFont(size=14)
    )
    footer.pack(pady=30)


# ---------------- LESSON SCREEN ----------------

def show_lesson():
    clear_screen()

    lesson_frame = ctk.CTkFrame(
        app,
        corner_radius=0
    )
    lesson_frame.pack(fill="both", expand=True)

    # Back button
    back_button = ctk.CTkButton(
        lesson_frame,
        text="<  Back",
        command=show_home,
        width=100,
        height=40,
        corner_radius=12
    )
    back_button.place(x=30, y=30)

    # Title
    title = ctk.CTkLabel(
        lesson_frame,
        text="ASL Lesson 1",
        font=ctk.CTkFont(
            size=38,
            weight="bold"
        )
    )
    title.pack(pady=(70, 5))

    subtitle = ctk.CTkLabel(
        lesson_frame,
        text="Learn 5 ASL fingerspelling signs",
        font=ctk.CTkFont(size=18)
    )
    subtitle.pack(pady=(0, 30))

    # Lesson card
    lesson_card = ctk.CTkFrame(
        lesson_frame,
        width=650,
        height=340,
        corner_radius=25
    )
    lesson_card.pack(pady=10)
    lesson_card.pack_propagate(False)

    signs_title = ctk.CTkLabel(
        lesson_card,
        text="Signs in this lesson",
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        )
    )
    signs_title.pack(pady=(30, 15))

    # Letters
    letters = ctk.CTkLabel(
        lesson_card,
        text="A     B     I     L     Y",
        font=ctk.CTkFont(
            size=40,
            weight="bold"
        )
    )
    letters.pack(pady=15)

    description = ctk.CTkLabel(
        lesson_card,
        text=(
            "Your camera will recognize your hand shape\n"
            "and give you real-time feedback."
        ),
        font=ctk.CTkFont(size=16),
        justify="center"
    )
    description.pack(pady=15)

    camera_button = ctk.CTkButton(
        lesson_card,
        text="Start Camera Practice",
        command=camera_test,
        width=280,
        height=55,
        corner_radius=15,
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        )
    )
    camera_button.pack(pady=20)


# ---------------- CAMERA TEST ----------------

def camera_test():
    print("Starting ASL camera practice...")

    subprocess.Popen(
        [sys.executable, "gesture_learning.py"]
    )


# ---------------- Start app ----------------

show_home()

app.mainloop()