from providers.financialtimes import _add_flourish

FALLBACK_REFERENCE = {
    "type": "flourish",
    "fallbackImage": {
        "url": "https://images.ft.com/v3/image/raw/https%3A%2F%2Fpublic.flourish.studio%2Fvisualisation%2F29898095%2Fthumbnail%3FcacheBuster%3D994593?source=ft-app-api&width=1020&dpr=1",
        "height": 712,
        "width": 1020,
    },
}


def test_flourish_block_embeds_the_visualisation():
    content = _add_flourish(
        {"type": "flourish", "id": "29898095", "description": "", "data": {"referenceIndex": 0}},
        FALLBACK_REFERENCE,
    )

    assert 'src="https://public.flourish.studio/visualisation/29898095/embed"' in content
    assert 'style="aspect-ratio: 1020 / 712;"' in content


def test_flourish_block_recovers_the_id_from_the_fallback_image():
    content = _add_flourish(
        {"type": "flourish", "id": "https://www.ft.com/flourish/29898095", "data": {"referenceIndex": 0}},
        FALLBACK_REFERENCE,
    )

    assert 'src="https://public.flourish.studio/visualisation/29898095/embed"' in content


def test_flourish_block_falls_back_to_the_fallback_image():
    content = _add_flourish(
        {"type": "flourish", "flourishType": "story", "data": {"referenceIndex": 0}},
        {"type": "flourish", "fallbackImage": {"url": "https://images.ft.com/thumbnail.png"}},
    )

    assert content == '<figure><img src="https://images.ft.com/thumbnail.png"></figure>'


def test_flourish_block_escapes_its_description():
    content = _add_flourish(
        {"type": "flourish", "id": "29898095", "description": 'a "chart" & <b>more</b>', "data": {"referenceIndex": 0}},
        FALLBACK_REFERENCE,
    )

    assert 'title="a &quot;chart&quot; &amp; &lt;b&gt;more&lt;/b&gt;"' in content


def test_flourish_block_without_any_visualisation():
    assert _add_flourish({"type": "flourish", "flourishType": "story", "data": {"referenceIndex": 0}}, {"type": "flourish"}) == ""
