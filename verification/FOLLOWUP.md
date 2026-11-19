# Sidebar and administrator password follow-up

**Observed (source):** The decorative sidebar wave used font glyphs separated by spaces and letter spacing. It was replaced with eight CSS bars inside a bounded flex container, marked aria-hidden. The note text is slightly smaller; the decoration is hidden below 781 pixels of desktop height and on mobile. Fixed desktop sidebars scroll internally when their contents exceed the available height, while navigation/profile elements retain their sizes.

**Observed:** The frontend production build passed after the change. This is compilation evidence, not browser behavior evidence. Command: `python verification/runtime.py frontend-build`; underlying npm command/working directory and exit 0 are in commands.jsonl and logs/frontend-build.log.

**Observed:** Real Edge browser checks passed for six application routes (Discover, Browse, Likes, Playlists, Recent, Admin) at eight viewport sizes: 1440x960, 1280x800, 1280x720, 1024x600, 900x480, 751x600, 750x844, 390x844. All 48 route/viewport checks established no horizontal page overflow, decorative bars within sidebar bounds when visible, no note/profile overlap, sign-out clear of the player, and no page errors. Evidence: sidebar-results.json and logs/sidebar-layout.log. Screenshots remain in ignored verification/runtime/.

**Observed:** The user changed adminPassword in the private local secrets file. The new value met the configured limits but login initially returned 401 because the existing administrator hash was unchanged. At the user's request, the isolated local administrator hash was updated with BCrypt, Spring was restarted, login returned 200, and /auth/me returned ADMIN. No password or hash was printed to logs. Evidence: logs/admin-password-restart.log and commands.jsonl.

**Observed:** Sidebar browser checks were repeated after the restart with the changed administrator password. The local account's private rollback hash is kept under ignored verification/runtime/ and excluded from publishing.

**Observed:** Public metadata was inspected for pretrained Essentia Discogs400, MTG-Jamendo genre, and a Wav2Vec2 GTZAN classifier. Sources, their required input formats, and integration recommendations are in docs/PRETRAINED_GENRE.md.

**Unverified:** No pretrained weights were installed or run; the application's genre prediction remains explicitly PLACEHOLDER. Existing feature extraction and recommendation behavior were not changed.
