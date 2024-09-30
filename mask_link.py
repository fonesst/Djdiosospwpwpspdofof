import urllib.parse

def masklink(link_input):
        masked_links = [
            "[Google]\n  ↳ https://www.google.com/url?q=" + urllib.parse.quote(link_input),
            "[YouTube]\n  ↳ https://www.youtube.com/redirect?q=" + urllib.parse.quote(link_input),
            "[VK]\n  ↳ https://vk.com/away.php?photo435_33&to=" + urllib.parse.quote(link_input),
            "[Facebook]\n  ↳ https://l.facebook.com/l.php?u=" + urllib.parse.quote(link_input),
            "[Ok RU]\n  ↳ https://m.ok.ru/dk?__dp=y&_prevCmd=altGroupMain&st.cln=off&st.cmd=outLinkWarning&st.rfn=" + urllib.parse.quote(link_input),
            "[Raidforums]\n  ↳ https://raidforums.com/misc.php?action=safelinks&url=" + urllib.parse.quote(link_input)
        ]
        return "\n\n".join(masked_links)