import httpx, traceback
from .selectors import Selector

class Clients:
    web = "WEB"
    mobile_web = "MWEB"
    tv = "TVHTML5"

class Feed:
    home = "FEwhat_to_watch"
    home2019 = "FEwhat_to_watch MODS=2016-2019"
    watch = "EPget_watch"
    shorts = "EPreel_watch"
    hashtag = "FEhashtag"

class CategoryEnumItem:
    def __init__(self, category):
        self.cat = category

    def __repr__(self):
        return f"<enum item {self.cat!r} from enum 'Category'>"

class VisibilityEnumItem:
    def __init__(self, unlisted, private):
        self.state = "Private" if private else ("Unlisted" if unlisted else "Visible")

    def __repr__(self):
        return f"<enum item {self.state!r} from enum 'Visibility'>"

selectors = {
    "web_video_title": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["title"].runsOrSimpleText,
    "web_video_description": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["description"].runsOrSimpleText,
    "web_video_length": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["lengthSeconds"].asFloat,
    "web_video_like_count": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["likeCount"].asInt,
    "web_video_view_count": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["viewCount"].asInt,
    "web_video_coauthors": Selector("web")[1]["watchNextResponse"]["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"]
        [1]["videoSecondaryInfoRenderer"]["subscribeButton"]["subscribeButtonRenderer"]["onSubscribeEndpoints"][0]["showDialogCommand"]
        ["panelLoadingStrategy"]["inlineContent"]["dialogViewModel"]["customContent"]["listViewModel"]["listItems"],
    "web_video_author": Selector("web")[0]["playerResponse"]["videoDetails"]["channelId"],
    "web_video_hashtags": Selector("web")[1]["watchNextResponse"]["contents"]["twoColumnWatchNextResults"]["results"]
        ["results"]["contents"][0]["videoPrimaryInfoRenderer"]["superTitleLink"]["runs"],
    "web_video_keywords": Selector("web")[0]["playerResponse"]["videoDetails"]["keywords"],
    "web_video_date": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["uploadDate"].isoDate,
    "web_video_category": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["category"],
    "web_video_safe_video": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["isFamilySafe"],
    "web_video_state_unlisted": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["isUnlisted"],
    "web_video_state_private": Selector("web")[0]["playerResponse"]["videoDetails"]["isPrivate"],
    "web_video_likable": Selector("web")[0]["playerResponse"]["videoDetails"]["allowRatings"],
    "web_video_crawlable": Selector("web")[0]["playerResponse"]["videoDetails"]["isCrawlable"],
    "web_video_movie": Selector("web")[0]["playerResponse"]["videoDetails"]["isTvfilmVideo"],
    "web_video_yttv": Selector("web")[0]["playerResponse"]["videoDetails"]["isUnpluggedCorpus"],
    "web_video_red": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["hasYpcMetadata"],
    "web_video_shorts": Selector("web")[0]["playerResponse"]["microformat"]["playerMicroformatRenderer"]["isShortsEligible"],
    "web_video_allow_ratings": Selector("web")[0]["playerResponse"]["videoDetails"]["allowRatings"],
    "web_shorts_sound_name": Selector("web")[2]["overlay"]["reelPlayerOverlayRenderer"]["playerOverlay"]["reelPlayerOverlayViewModel"]
        ["actionBar"]["reelActionBarViewModel"]["buttonViewModels"][-1]["pivotButtonViewModel"]["soundAttributionTitle"]["content"],
    "web_shorts_sound_img": Selector("web")[2]["overlay"]["reelPlayerOverlayRenderer"]["playerOverlay"]["reelPlayerOverlayViewModel"]
        ["actionBar"]["reelActionBarViewModel"]["buttonViewModels"][-1]["pivotButtonViewModel"]["thumbnail"]["sources"][0]["url"],
    "web_shorts_sound_id": Selector("web")[2]["engagementPanels"][-1]["engagementPanelSectionListRenderer"]["content"]["richGridRenderer"]
        ["header"]["pageHeaderViewModel"]["title"]["dynamicTextViewModel"]["rendererContext"]["commandContext"]["onTap"]
        ["innertubeCommand"]["reelWatchEndpoint"]["videoId"],
    "web_channel_name": Selector("web")["microformat"]["microformatDataRenderer"]["title"],
    "web_channel_avatar": Selector("web")["metadata"]["channelMetadataRenderer"]["avatar"]["thumbnails"][0]["url"],
    "web_video_related_sections": Selector("web")[1]["watchNextResponse"]["contents"]["twoColumnWatchNextResults"]
        ["secondaryResults"]["secondaryResults"]["results"],
    "web_video_sdata": Selector("web")[0]["playerResponse"]["streamingData"],
    "web_channel_subsraw": Selector("web")["header"]["pageHeaderRenderer"]["content"]["pageHeaderViewModel"]["metadata"]["contentMetadataViewModel"]["metadataRows"][1]["metadataParts"][0]["text"]["content"],
    "web_home2019_shelves": Selector("web")["contents"]["sectionListRenderer"]["contents"],
}

def dig(obj, *path, default=None):
    for key in path:
        if isinstance(key, int):
            if not isinstance(cur := obj, (list, tuple)) or key >= len(cur):
                return default
            obj = cur[key]
        else:
            if not isinstance(obj, dict) or key not in obj:
                return default
            obj = obj[key]
    return default if obj is None else obj


def pick(*values):
    return next((v for v in values if v), None)


def parse_lockup(item):
    lm = item.get("lockupViewModel")
    if not lm:
        return None

    ctype = lm.get("contentType", "")
    if ctype not in ("LOCKUP_CONTENT_TYPE_VIDEO",
                     "LOCKUP_CONTENT_TYPE_ALBUM",
                     "LOCKUP_CONTENT_TYPE_PLAYLIST"):
        return None

    is_video = ctype == "LOCKUP_CONTENT_TYPE_VIDEO"

    thumb = pick(
        dig(lm, "contentImage", "thumbnailViewModel", "image", "sources", 0, "url"),
        dig(lm, "contentImage", "collectionThumbnailViewModel",
            "primaryThumbnail", "thumbnailViewModel", "image", "sources", 0, "url"),
    )

    if is_video:
        duration = pick(
            dig(lm, "contentImage", "thumbnailViewModel", "overlays", 0,
                "thumbnailBottomOverlayViewModel", "badges", 0,
                "thumbnailBadgeViewModel", "text"),
            dig(lm, "contentImage", "thumbnailViewModel", "overlays", 0,
                "thumbnailOverlayBadgeViewModel", "thumbnailBadges", 0,
                "thumbnailBadgeViewModel", "text"),
        )
    else:
        duration = dig(lm, "contentImage", "collectionThumbnailViewModel",
                       "primaryThumbnail", "thumbnailViewModel", "overlays", 0,
                       "thumbnailOverlayBadgeViewModel", "thumbnailBadges", 0,
                       "thumbnailBadgeViewModel", "text")

    rows = dig(lm, "metadata", "lockupMetadataViewModel",
               "metadata", "contentMetadataViewModel", "metadataRows") or []
    author = views = date = None
    for row in rows:
        text = dig(row, "metadataParts", 0, "text", "content")
        if not text or "playlist" in text.lower():
            continue
        if author is None:
            author = text
        elif views is None and text[0].isdigit():
            views = text
        elif date is None:
            date = text

    return {
        "id": lm.get("contentId"),
        "kind": "video" if is_video else "album",
        "title": dig(lm, "metadata", "lockupMetadataViewModel", "title", "content"),
        "author": author,
        "views": views,
        "date": date,
        "duration": duration,
        "thumb": thumb,
        "verified": is_verified(lm),
    }

class Sound:
    """SOUND / Replace this to real docstring in the file."""
    def __init__(self, response):
        self.name = selectors["web_shorts_sound_name"].apply(response)
        self.imageURL = selectors["web_shorts_sound_img"].apply(response)
        self.id = selectors["web_shorts_sound_id"].apply(response)
        #print(selectors["web_shorts_sound_id"].err)

    def __repr__(self):
        return self.name

class Channel:
    """CHANNEL / Replace this to real docstring in the file."""
    def __init__(self, response, id, client):
        self.id = id
        self.title = selectors["web_channel_name"].apply(response)
        self._subscribers_raw = selectors["web_channel_subsraw"].apply(response).removesuffix("subscribers").rstrip() if selectors["web_channel_subsraw"].apply(response) else "0"
        self.avatar = selectors["web_channel_avatar"].apply(response)

    def __repr__(self):
        return f"<channel with id='UC{self.id}'>"

def is_verified(lockup):
    try:
        runs = (lockup["metadata"]["lockupMetadataViewModel"]["metadata"]
                      ["contentMetadataViewModel"]["metadataRows"][0]
                      ["metadataParts"][0]["text"]
                      .get("attachmentRuns", []))
    except (KeyError, TypeError, IndexError):
        return False

    for run in runs:
        try:
            name = (run["element"]["type"]["imageType"]["image"]
                       ["sources"][0]["clientResource"]["imageName"])
        except (KeyError, TypeError, IndexError):
            continue
        if name == "CHECK_CIRCLE_FILLED":
            return True
    return False

class Video:
    """VIDEO / Replace this to real docstring in the file."""
    def __init__(self, response, id, client):
        self.id = id
        self.title = selectors["web_video_title"].apply(response)
        self.description = selectors["web_video_description"].apply(response)
        if self.description == None:
            self.description = ""
        self.duration = selectors["web_video_length"].apply(response)
        self._allow_ratings = selectors["web_video_allow_ratings"].apply(response)
        self.likes = selectors["web_video_like_count"].apply(response) if self._allow_ratings else 0
        self.views = selectors["web_video_view_count"].apply(response)
        self.authors = \
            [GetChannels.get(client.channels, item["listItemViewModel"]["title"]["commandRuns"][0]["onTap"]["innertubeCommand"]["browseEndpoint"]["browseId"].removeprefix("UC")) for item in selectors["web_video_coauthors"].apply(response) or []] \
            or [GetChannels.get(client.channels, selectors["web_video_author"].apply(response).removeprefix("UC") if selectors["web_video_author"].apply(response) else "hhpVpIbX_6xJv-qlbatVMw")]
        #print(selectors["web_video_coauthors"].err)
        self.hashtags = [run["text"].removeprefix("#") for run in selectors["web_video_hashtags"].apply(response) or [] if run.get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId") == Feed.hashtag]
        self.keywords = selectors["web_video_keywords"].apply(response)
        if self.keywords == None:
            self.keywords = []
        self.date = selectors["web_video_date"].apply(response)
        self.category = CategoryEnumItem(selectors["web_video_category"].apply(response))
        self.safe_video = selectors["web_video_safe_video"].apply(response)
        self.visibility = VisibilityEnumItem(selectors["web_video_state_unlisted"].apply(response), selectors["web_video_state_private"].apply(response))
        self.likeable = selectors["web_video_likable"].apply(response)
        self.crawlable = selectors["web_video_crawlable"].apply(response)
        self.is_movie = selectors["web_video_movie"].apply(response)
        self.is_youtube_tv = selectors["web_video_yttv"].apply(response)
        self.is_premium = selectors["web_video_red"].apply(response)
        self._related = [
            parsed for parsed in (
                parse_lockup(item)
                for item in (selectors["web_video_related_sections"].apply(response) or [])
            )
            if parsed is not None
        ]
    def __repr__(self):
        return f"<video '{self.title}' with id={self.id}>"

class Shorts(Video):
    """SHORTS / Replace this to real docstring in the file."""
    def __init__(self, response, id, client):
        super().__init__(response, id, client)
        self.sound = Sound(response)

def payload(name, client, **kwargs):
    payload = {
        "context": client.context
    }

    if name == Feed.watch:
        payload = {
            "context": client.context,
            "playerRequest": {
                "videoId": kwargs["id"],
                "playbackContext": {
                    "contentPlaybackContext": {
                        "currentUrl": f"/watch?v={kwargs["id"]}",
                        "splay": False,
                        "autoCaptionsDefaultOn": False,
                        "autonavState": "STATE_OFF",
                        "html5Preference": "HTML5_PREF_WANTS"
                    },
                    "devicePlaybackCapabilities": {
                        "supportsVp9Encoding": True,
                        "supportXhr": True,
                    },
                },
                "racyCheckOk": True,
                "contentCheckOk": True
            },
            "watchNextRequest": {
                "videoId": kwargs["id"],
                "racyCheckOk": True,
                "contentCheckOk": True,
                "autonavState": "STATE_OFF",
                "captionsRequested": False,
            },
        }
    elif name == Feed.shorts:
        payload = {
            "context": client.context,
            "playerRequest": {
                "videoId": kwargs["id"],
            },
            "disablePlayerResponse": True
        }
    elif name == Feed.home2019:
        return {
            "context": {
                "client": {
                    "clientName": "16",
                    "clientVersion": "1.0",
                    "hl": client.context["client"]["hl"],
                    "gl": client.context["client"]["gl"],
                },
                "user": {"lockedSafetyMode": False},
                "request": {"useSsl": True},
            },
            "browseId": Feed.home,
        }
    elif name.startswith("UC"):
        payload = {
            "context": client.context,
            "browseId": name
        }

    return payload

def endpoint(name, client, **kwargs):
    payload_ = payload(name, client, **kwargs)
    if name == Feed.watch:
        name = "get_watch"
    elif name == Feed.shorts:
        name = "reel/reel_item_watch"
    else:
        name = "browse"

    return client._http.post(f"/youtubei/v1/{name}?prettyPrint=false", json=payload_)

class GetVideos:
    """GET VIDEOS / Delete this class in the file."""
    def __init__(self, client):
        self._client = client

    def get(self, video_id):
        r = endpoint(Feed.watch, self._client, id=video_id)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            error = r.json()
            print(error)
            traceback.print_exc()
            return {}  # ерор
        data = r.json()
        if selectors["web_video_shorts"].apply(data):
            shorts_data = endpoint(Feed.shorts, self._client, id=video_id)  # я и хотел в 2 раза медленнее
            data.append(shorts_data.json())
            return Shorts(data, video_id, self._client)
        return Video(data, video_id, self._client)

class GetChannels:
    """GET CHANNELS / Delete this class in the file."""
    def __init__(self, client):
        self._client = client

    def get(self, channel_id):
        r = endpoint("UC" + channel_id if not channel_id.startswith("UC") else channel_id, self._client)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            error = r.json()
            print(error)
            return {}  # ерор
        data = r.json()
        return Channel(data, channel_id, self._client)

class Client:
    """CLIENT / Delete this class in the file."""
    def __init__(self):
        self.name = Clients.web
        self.version = "2.20260918.00.00"

class ConfigClient:
    def __init__(self):
        self.client = Client()
        self._language = "en-US"
        self._hlgl = self.language.split("-")
        self._http = httpx.Client(
            base_url="https://www.youtube.com",
            timeout=10.0,
            headers=self.headers,
        )
        self._http.post("/")  # Init keep-alive
        self.videos = GetVideos(self)
        self.channels = GetChannels(self)

    @property
    def context(self):
        return {
            "client": {
                "clientName": self.client.name,
                "clientVersion": self.client.version,
                "hl": self._hlgl[0],
                "gl": self._hlgl[1],
            }
        }

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, val):
        self._language = val
        self._hlgl = val.split("-")

    @property
    def lower_name(self):
        return self.client.name.lower()

    def _algVideos(self, shelves=False):
        if not shelves:
            raise NotImplementedError

        data = endpoint(Feed.home2019, self).json()

        sections = (
            data.get("contents", {})
                .get("sectionListRenderer", {})
                .get("contents")
        )

        out = []
        for entry in sections or []:
            for c in (entry.get("itemSectionRenderer", {}).get("contents")
                      or [entry]):
                shelf = c.get("shelfRenderer")
                if not shelf:
                    continue

                t = shelf.get("title") or {}
                title = t.get("simpleText") or (
                    "".join(r.get("text", "") for r in t.get("runs") or [])
                    or None
                )

                content = shelf.get("content") or {}
                items = next(
                    (content[k].get("items") for k in (
                        "horizontalListRenderer",
                        "verticalListRenderer",
                        "expandedShelfContentsRenderer",
                        "listRenderer",
                        "gridRenderer",
                    ) if k in content and content[k].get("items") is not None),
                    [],
                )

                videos = []
                for it in items:
                    v = (it.get("compactVideoRenderer")
                         or it.get("videoRenderer")
                         or it.get("gridVideoRenderer")
                         or it.get("playlistVideoRenderer")
                         or it.get("richItemRenderer", {}).get("content", {})
                             .get("videoRenderer"))
                    if v and v.get("videoId"):
                        videos.append(v["videoId"])

                out.append({
                    "title": title,
                    "videos": videos,
                    "count": len(videos),
                    "raw": shelf,
                })

        return out

    @property
    def headers(self):
        return {
            "Content-Type": "application/json",
            "X-Youtube-Client-Name": self.client.name,
            "X-Youtube-Client-Version": self.client.version,
        }