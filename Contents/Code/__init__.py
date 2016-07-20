# Hegre-Art
import re
import urllib2
from HTMLParser import HTMLParser

# URLS
INFO_URL_BASE = 'http://www.hegre-art.com/'
POSTER = 'http://cache.updates.hegre-art.com/films/%s/%s-poster-640x.jpg'
MODEL_PHOTO = 'http://cache.updates.hegre-art.com/models/%s/%s-poster-800x.jpg' 
#EX: http://cache.updates.hegre-art.com/models/darina_l/darina_l-poster-800x.jpg
GOOGLE_JSON_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=large&q=%s'   #[might want to look into language/country stuff at some point] param info here: http://code.google.com/apis/ajaxsearch/documentation/reference.html

def Start():
	HTTP.CacheTime = CACHE_1WEEK 
	HTTP.SetHeader('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')

class  HAAgent(Agent.Movies):
	name = 'Hegre-Art'
	languages = [Locale.Language.English]
	accepts_from = ['com.plexapp.agents.localmedia']
	primary_provider = True

	def search(self, results, media, lang):
		Log('########################SEARCH########################');

		#Setup name
		name = media.title
		if media.primary_metadata is not None:
			name = media.primary_metadata.title
		name = re.sub(r'\[.+?\]', '', name) # Remove anything in brackets		  
		normalizedName = String.StripDiacritics(name)
		
		jsonURL = GOOGLE_JSON_URL % String.Quote('' + normalizedName + ' site:hegre-art.com', usePlus=True)
		
		Log(jsonURL)
		
		googleJSON = JSON.ObjectFromURL(jsonURL)
		Log(googleJSON)
		
		searchResults = googleJSON['responseData']['results']
		score = 100
		for result in searchResults:
			url = result['unescapedUrl']
			if url.count('hegre-art.com') > 0:
				urlSlug = url.replace(INFO_URL_BASE,'').replace('/',':')
				Log('urlSlug: '+urlSlug)
				
				results.Append(MetadataSearchResult(
					id    = urlSlug,
					name  = HTMLParser().unescape(result['titleNoFormatting']),
					score = score,
					lang  = lang
					))
				
				score = score-10 #Decriment score of next result
			results.Sort('score', descending=True)

	def update(self, metadata, media, lang):
		Log('########################UPDATE########################');
				
		Log('id: '+metadata.id)
		
		# Reconstruct URL from slug
		url = INFO_URL_BASE + metadata.id.replace(':','/')
		Log('Loading info page: '+url)
		
		html = HTML.ElementFromURL(url)
		urlSlug = metadata.id
				
		metadata.title = url.split('/')[-1].replace('&','%26').replace('-',' ').title()

		Log('Title: '+metadata.title)
		
		# Get Thumb and Poster
		try:	  
			slug = metadata.title.replace(' ', '')
			posterUrl = POSTER % (slug, slug)
			if not urlExists(posterUrl):
				Log('Thumb doesn\'t exist! Trying alternate.')
				slug = metadata.title.lower().replace(' ','-')
				posterUrl = POSTER % (slug, slug)
				
			if urlExists(posterUrl):
				metadata.posters[posterUrl] = Proxy.Preview(posterUrl)
				Log('Image: '+posterUrl)
				
		except: pass

		# Title.
		try:
			metadata.title = html.xpath("//h1")[0].text_content().strip()
			Log('Title from page is: '+metadata.title)
		except: pass
		
		# Genre.
		try:
			metadata.genres.clear()
			genres = html.xpath('//a[@class="tag"]/text()')

			for genre in genres:
				metadata.genres.add(genre)
				Log('genre: '+genre)
		except: pass
		
		# Tagline.
		try: 
			metadata.tagline = ''
			metadata.tagline = html.xpath("//div[@class='record-description-content record-box-content']")[0][0].text_content().strip()
		except: pass

		# Summary.
		try:
			metadata.summary = ""
			
			try: 
				filmSummary = html.xpath("//div[@class='massage-copy']")[0].text_content().strip()					
				metadata.summary = filmSummary
			except: pass
			
			try: 
				massageSummary = html.xpath("//div[@class='massage-text']")[0].text_content().strip()
				
				massageBottom = html.xpath("//div[@class='massage-bottomline']")[0].text_content().strip()
					
				metadata.summary = massageSummary+'\n'+massageBottom
			except: pass
			
		except: pass

		# Release Date
		try:
			release_date = html.xpath("//div[@class='date-and-covers']")[0].text_content().strip()
			metadata.originally_available_at = Datetime.ParseDate(release_date).date()
			metadata.year = metadata.originally_available_at.year
		except: pass

		# Starring
		try:
			metadata.roles.clear()
			
			Log('Starring:')
			stars = html.xpath('//a[@class="record-model"]/@href')
			
			for star in stars:
				star = star.replace('/models/','').replace('-',' ')
				name = star.title()
				
				picSlug = star.replace(' ', '_')
				photoUrl = MODEL_PHOTO % (picSlug,picSlug)
				Log('photo Url: '+photoUrl)
				
				role = metadata.roles.new()
				role.actor = name
				role.photo = photoUrl
				# actorThumbUrl = EXC_STAR_PHOTO % role.actor.replace(' ', '_')
				# actorThumb = HTTP.Request(actorThumbUrl)
				# role.photo = Proxy.Preview(actorThumb)

				Log('Starring: ' + role.actor)
		except: pass

		# Studio
		metadata.studio = "Hegre-Art"
		
def urlExists(url):
	Log('checking existence of: '+url)
	try: 
		urllib2.urlopen(urllib2.Request(url))
		return True
	except: return False
		