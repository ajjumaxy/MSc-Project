"""
File: GlassdoorScraper.py
Author: Daniel Stancl
"""

# import libraries
import time
import datetime
from datetime import date
import re
import numpy as np
import pandas as pd
import django
import json
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

## CLASS
class GlassdoorScraper(object):
    """
    The major purpose of this class is to scrape reviews from Glassdoor.
    As such, all actions which are necessary during the browsing of the web are defined throughout this class.
    Subsequently, this class can save the data either as csv/xlsx file using pandas, or the data can be sent to django dataabse.
    """
    #####################
    ### MAGIC METHODS ###
    #####################

    def __init__(self, chrome_driver_path, account_type, email, password,
                headless_browsing, review_writer, max_review_age, url):
        """
        Instantiate method handling all the necessary setting.
        :param path_chrome_drive: An absolute path to a ChromeDriver.
        :param email: Email used for log in to the Glassdoor account; type=str
        :param password: Password used for log in to the Glassdoor account; type=str
        :param headless_browsing: If True, `headless` browsing is to be used.
        :param review_writer:
            This django Model base that is used for writing and storing the data in a given database;
            type=django.db.models.base.ModelBase
        :param max_review_age: An indication how old reviews are to be scraped; type=int|float
        :param url: A URL to the review page of Glassdoor webpages; type=str
        """
        # configure driver & chromeoptions
        self.chrome_driver_path=chrome_driver_path
        self.chrome_options = webdriver.ChromeOptions()
        self.headless_browsing = headless_browsing
        if headless_browsing:
            self.chrome_options.add_argument('--headless')
            self.chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(
            executable_path=chrome_driver_path,
            options=self.chrome_options
        )

        if (not headless_browsing):
            self.driver.set_window_size(1440, 1080)
            self.driver.set_window_position(0,0)
        
        # set the time limit after selenium driver should be reopen and a robot should re-log in glassdor
        self.limit_to_reload = 3*60*60 # 3 hours
        
        # store url, email
        self.url = url
        self.email = email
        self.password = password

        # Instantiate empty dataframe for storing reviews
        self.schema = [
            'CompanyID', 'Company', 'ReviewTitle',
            'Year', 'Month', 'Day', 'Rating',
            'JobTitle', 'Location', 'Recommendation',
            'Outlook', 'OpinionOfCEO', 'Contract',
            'ContractPeriod', 'Pros', 'Cons',
            'AdviceToManagement', 'Timestamp'
        ]
        self.data = []

        # a dictionary for converting three-letter months into an integer
        self.monthToInt = {
            'Jan': 1, 'Feb': 2, 'Mar': 3,
            'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9,
            'Oct': 10, 'Nov': 11, 'Dec': 12
        }   

        # get current date so that scraping can be stop w.r.t. date
        self.current_date = date.today()
        self.max_review_age = max_review_age # how old reviews might be

        # sanity checks
        assert type(email)==str, 'Param email must be a type of str'

        if review_writer:
            assert type(review_writer) == django.db.models.base.ModelBase, 'param CompanyWritert must be of type django.db.models.base.ModelBase!'
            self.ReviewWriter = review_writer
            self.reviewWriterIsUsed = True

    def __reload__(self, location, url_to_return):
        """
        A function that is responsible for the following steps:
            1. It closes all current windows.
            2. It re-logs in to Glassdoor
        This procedure is held in order a robot will not be kicked out of glassdoor.
        This procedure takes place once a pre-define time limit is exceeded.
        
        :param location:
        :param url_to_return:
        """
        self.driver.quit()
        self.driver = webdriver.Chrome(
            executable_path=self.chrome_driver_path,
            options=self.chrome_options
        )
        if (not self.headless_browsing):
            self.driver.set_window_size(1440, 1080)
            self.driver.set_window_position(0,0)
        
        self.getOnReviewsPage(self.company_name, location)
        self.getURL(url_to_return)

    ######################
    ### PUBLIC METHODS ###
    ## major func first ##
    # alphabetical order #
    ######################

    def scrape(self, company_name, location, 
                limit = float(np.inf)):
        """
        MAIN FUNCTION (tba)
        In this case, data are stored gradually because they might require a relatively large amount of space. This is a difference from WikiYahooScraper.
        :param company_name: type=str
        :param location: city; type=str
        :param limit: number of pages to be scraped; type=int
        """
        if self.reviewWriterIsUsed == True:
            # make self.data to be always an empty list if they are to be written into django db
            self.data = []
        self.company_name = company_name # store company_name
        
        scraping_startTime = time.time()
        while (self.page <= limit) & (self._isNextPageAvailable()) & (self._newerThanGivenYears()):
            self._clickContinueReading()
            self.getReviews()           
            self.data.extend(
                [self.parseReview(review) for review in self.reviews]
            )
            self._goNextPage()
            
            if (time.time() - scraping_startTime) > self.limit_to_reload:
                self.__reload__(location=location, url_to_return=self.driver.current_url)
                scraping_startTime = time.time()
            t = time.time() - scraping_startTime
            print(self.page, t)
        
        # store the data if they are to be stored in django DB
        if self.reviewWriterIsUsed == True:
            [self._writeRowToDjangoDB(datarow) for datarow in self.data]

    def acceptCookies(self):
        """
        Accept cookies consent if displayed.
        """
        try:
            self.driver.find_element_by_id('onetrust-accept-btn-handler').click()
        except:
            print('No cookies consent is required to accept.')
    
    def getOnReviewsPage(self, company_name, location):
        """
        Function that get users at on the first page of reviews for a given company.
        :param company_name: type=str
        :param location:
        """
        try:
            self.sign_in()
            time.sleep(3)
        except:
            time.sleep(2)

        self.company_name = company_name
        self.getURL(self.url)
        self.searchReviews(company_name, location)
        if self._isNotUniqueSearchResult():
            self._selectFirstCompany()
        self._clickReviewsButton()
        time.sleep(2)

        self._sortReviewsMostRecent()
        
    def getURL(self, url):
        """
        Get on URL and then sleep for a while to make sure web content to be loaded properly.
        """
        self.driver.get(url)
        time.sleep(1)
    
    def getReviews(self):
        """
        A function returning a list of WebElements corresponding to individual 
        reviews displayed on a given page.
        There are two classes of empReview hence must be collected in two steps.
        *It might be moved to private functions*
        """
        self.reviews = self.driver.find_elements_by_xpath('//li[@class="empReview cf"]')
        self.reviews.extend(self.driver.find_elements_by_xpath('//li[@class="noBorder empReview cf"]'))    
   
    def saveToCSV(self, path):
        """
        :patam path:
        """
        if self.reviewWriterIsUsed == True:
            print(f'Data cannot be saved to {path} as they have continuosly pushed to django database.')
        pd.DataFrame(
            self.data,
            columns=self.schema
        ).to_csv(path)

    def saveToExcel(self, path):
        """
        :param path:
        """
        if self.reviewWriterIsUsed == True:
            print(f'Data cannot be saved to {path} as they have continuosly pushed to django database.')
        pd.DataFrame(
            self.data,
            columns=self.schema
        ).to_excel(path)
    
    def searchReviews(self, company_name, location):
        """
        A function that is responsible for searching company's reviews
        once a user is on a main review page.
        *It might be moved to private functions*
        :param company_name: type=str
        :param location: type=str
        """
        try:
            self._fillCompanyName(company_name)
            self._fillLocation(location)
            self._clickSearchButton()
        except:
            self._fillCompanyNameSecondary(company_name)
            self._fillLocationSecondary(location)
            self._closeAddResumeWindow()
            self._clickSearchButtonSecondary()
        self.page = 1
        time.sleep(1)

    def sign_in(self):
        """
        """
        login_url='https://www.glassdoor.com/profile/login_input.htm'
        self.getURL(login_url)
        
        self.driver.find_element_by_name('username').send_keys(self.email)
        self.driver.find_element_by_name('password').send_keys(self.password)
        self.driver.find_element_by_xpath('//button[@type="submit"]').click()

        print('Login was successful.')
    
    def parseReview(self, review):
        """
        Parse a whole single review into individual elements listed below:
            'ReviewTitle', 'Timestamp', 'Rating', 'JobTitle', 'Location',
            'RecommendationBar', 'MainText', 'Pros', 'Cons', 'Advice 
            to Managemet'
        :param review: WebElement
        """
        self._getReviewHTML(review) # create self.reviewHTML object
        self._parseReviewElements()
        
        return {
            'Company': self.company_name,
            'ReviewTitle': self._getReviewTitle(),
            'Year': self._getTimestamp(element='Year'),
            'Month': self._getTimestamp(element='Month'),
            'Day': self._getTimestamp(element='Day'),
            'Rating': self._getRating(),
            'JobTitle': self._getJobTitle(),
            'EmployeeRelationship': self._getEmployeeRelationship(),
            'Location': self._getLocation(),
            'Recommendation': self._getRecommendationBar(element='Recommendation'),
            'Outlook': self._getRecommendationBar(element='Outlook'),
            'OpinionOfCEO': self._getRecommendationBar(element='OpinionOfCEO'),
            'Contract': self._getContract(),
            'ContractPeriod': self._getContractPeriod(),
            'Pros': self._getReviewBody(element='Pros'),
            'Cons': self._getReviewBody(element='Cons'),
            'AdviceToManagement': self._getReviewBody(element='Advice to Management'),
            'Timestamp': timezone.now()
        }
    
    #######################
    ### PRIVATE METHODS ###
    ## alphabetical order #
    #######################

    def _clickContinueReading(self):
        """
        Click "Continue reading" button to unroll the whole version of reviews.
        """
        while len(self._getContinueReadingList()) > 0:
            continueReadingPresent = 0
            while continueReadingPresent == 0:
                try:
                    self._getContinueReadingList()[0].click()
                    continueReadingPresent += 1
                except:
                    time.sleep(1)
            time.sleep(5)
    
    def _clickReviewsButton(self):
        """
        Click "Reviews" button on a company's profile to dislay the first review page.
        """
        self.driver.find_element_by_xpath('//*[@id="EIProductHeaders"]/div/a[1]').click()

    def _clickSearchButton(self):
        """
        Click "Search" button to trigger search for a company's profile.
        """
        self.driver.find_element_by_class_name("gd-btn-mkt").click()
    
    def _clickSearchButtonSecondary(self):
        """
        Click "Search" button to trigger search for a company's profile.
        """
        try:
            self.driver.find_element_by_xpath('/html/body/div[7]/div/nav[1]/div/div/div/div[4]/div[3]/form/div/button').click()
        except:
            self.driver.find_element_by_xpath('/html/body/div[6]/div/nav[1]/div/div/div/div[4]/div[3]/form/div/button').click()

    def _closeAddResumeWindow(self):
        """
        Functionality closing 'Add resume' to complete the Glassdoor profile, as it hides 'search button'
        """
        try:
            self.driver.find_element_by_class_name('SVGInline-svg').click()
        except:
            pass

    def _fillCompanyName(self, company_name):
        """
        Fill a company name in a search field on the title page.
        :param company_name: type=str
        """
        assert type(company_name) == str, 'Param company_name must be a type of str.'
        self.driver.find_element_by_class_name("keyword").clear()
        self.driver.find_element_by_class_name("keyword").send_keys(company_name)

    def _fillCompanyNameSecondary(self, company_name):
        """
        There are 
        """
        assert type(company_name) == str, 'Param company_name must be a type of str.'
        self.driver.find_element_by_id("sc.keyword").clear()
        self.driver.find_element_by_id("sc.keyword").send_keys(company_name)


    def _fillEmailAndClick(self, email):
        """
        Fill a user e-mail to log in a Glassdoor account.
        :param email: type=str
        """
        assert type(email) == str, 'Param email must be a type of str.'
        self.driver.find_element_by_xpath('//*[@id="identifierId"]').clear()
        self.driver.find_element_by_xpath('//*[@id="identifierId"]').send_keys(email)
        self.driver.find_element_by_xpath('//*[@id="identifierNext"]/div/span/span').click()

    def _fillLocation(self, location):
        """
        Fill a company name in a search field on the title page.
        :param location: type=str
        """
        assert type(location) == str, 'Param locaation must be a type of str.'
        self.driver.find_element_by_class_name("loc").clear()
        self.driver.find_element_by_class_name("loc").send_keys(location)

    def _fillLocationSecondary(self, location):
        """
        """
        assert type(location) == str, 'Param locaation must be a type of str.'
        self.driver.find_element_by_id("sc.location").clear()
        self.driver.find_element_by_id("sc.location").send_keys(location)

    def _fillPassword(self):
        """
        """
        if self.password == None:
            self.driver.find_element_by_xpath('//*[@id="password"]/div[1]/div/div[1]/input').send_keys(input())
        else:
            self.driver.find_element_by_xpath('//*[@id="password"]/div[1]/div/div[1]/input').send_keys(self.password)

    def _fillPasswordAndClick(self):
        """
        Fill a user password to log in a Glassdoor account. Password is asked to be typed.
        """
        self.driver.find_element_by_xpath('//*[@id="password"]/div[1]/div/div[1]/input').clear()
        self._fillPassword()
        self.driver.find_element_by_xpath('//*[@id="passwordNext"]/span/span').click()

    def _getEmployeeRelationship(self):
        """
        Parse reviewer's employee relationship, i.e. a former or current one, from review-HTML if available. 
        :param reviewHTML: HTML code of a review page returned by a function _getReviewHTML, type=str
        """
        try:
            titleAndRelationshop = re.search('<span class="authorJobTitle middle">(.+?)</span>', self.reviewHTML).group(1)
            return titleAndRelationshop.split(' - ')[1]
        except:
            return None
    
    def _getContinueReadingList(self):
        """
        Get the most recent version of 'Continue reading' buttons on reviews page.
        """
        return self.driver.find_elements_by_xpath(
            '//div[@class="v2__EIReviewDetailsV2__continueReading v2__EIReviewDetailsV2__clickable"]'
        )
    
    def _getContract(self):
        """
        Parse information whether a reviewer is/was a full-time/part-time employee.
        """
        try:
            return [word for word in self.mainText.split() if 'time' in word][0]
        except:
            return None

    def _getContractPeriod(self):
        """
        Parse information how long a reviewr was/has been working for a company.
        """
        try:
            return re.search('for (.+)', self.mainText).group(1)
        except:
            return None
    
    def _getJobTitle(self):
        """
        Parse reviewer's job title from review-HTML if available.
        :param reviewHTML: HTML code of a review page returned by a function _getReviewHTML, type=str
        """
        try:
            titleAndRelationshop = re.search('<span class="authorJobTitle middle">(.+?)</span>', self.reviewHTML).group(1)
            return titleAndRelationshop.split(' - ')[0]
        except:
            return None
    
    def _getLocation(self):
        """
        Parse reviewr's job location from review-HTML if available.
        """
        try:
            return re.search('<span class="authorLocation">(.+?)</span>', self.reviewHTML).group(1)
        except:
            return None
    
    def _getRating(self):
        """
        Parse review rating from review-HTML if available.
        """
        try:
            return re.search('<div class="v2__EIReviewsRatingsStylesV2__ratingNum v2__EIReviewsRatingsStylesV2__small">(.+?)</div>', self.reviewHTML).group(1)
        except:
            return None

    def _getRecommendationBar(self, element):
        """
        Parse recomendation bar containing items/attributes like ('positive outlook', 'approves of CEO') etc.
        All the items are concatenated to a string by ' | '.
        """
        assert type(element) == str, 'Param element must be a type of str.'
        assert element in ['Recommendation', 'Outlook', 'OpinionOfCEO'], "Element must be drawn from the list ['Recommendation', 'Outlook', 'OpinionOfCEO']."
        return self.recommendationBar[element]

    def _getReviewBody(self, element):
        """
        Get individual elements of the review body
        :param element: A string indicating a component of a review body
            select from: ['Pros', 'Cons', 'Advice to Management'], type=str
        """
        assert type(element) == str, 'Param element must be a type of str.'
        assert element in ['Pros', 'Cons', 'Advice to Management'], "Element must be drawn from the list ['Pros', 'Cons', 'Advice to Management']."
        try:
            return self.parsedReviewBody[element]
        except:
            return None
    
    def _getReviewHTML(self, review):
        """
        Get attribute 'outerHTML' from a WebElement corresponding to a single review.
        :param review: WebElement
        """
        self.reviewHTML = review.get_attribute('outerHTML')

    def _getReviewTitle(self):
        """
        Parse review title from review-HTML if filled.
        """
        try:
            return re.search('reviewLink">"(.+?)"</a>', self.reviewHTML).group(1)
        except:
            return None

    def _getTimestamp(self, element):
        """
        Get a single element = Day | Month | Year; from a timestamp.
        :param element: draw from ['Day', 'Month', 'Year'], type=str
        """
        assert type(element) == str, 'Param element must be a type of str.'
        assert element in ['Day', 'Month', 'Year'], "Element must be drawn from the list ['Day', 'Month', 'Year']."
        if self.timestamp != 'Featured Review':
            if element == 'Day':
                return int(self.timestamp.split()[2])
            elif element == 'Month':
                return self.monthToInt[
                    self.timestamp.split()[1]
                ]
            elif element == 'Year':
                return int(self.timestamp.split()[3])
        else:
            return 0
    
    def _goNextPage(self):
        """
        """
        if '_P' in self.driver.current_url:
            next_url = re.sub('_P(.+?).htm', f'_P{(self.page)+1}.htm', self.driver.current_url)
        else:
            next_url = re.sub('.htm', '_P2.htm', self.driver.current_url)
        self.getURL(next_url)
        self.page += 1
        time.sleep(2)

    def _isNextPageAvailable(self):
        """
        Needs to be finished.
        The ultimate functionality is to find out whether the next page
        contains any review. If not, scraping should be terminated. 
        """
        self.getReviews()
        return len(self.reviews) > 0

    def _isNotUniqueSearchResult(self):
        """
        It might happen a list of companies is returned when a company name is searched.
        This is an identifier of such an occasion.
        """
        return len(self.driver.find_elements_by_id('SearchResults')) != 0

    def _loginRequired(self):
        """
        A function that is responsible for detecting whether a user is required to log in its Glassdoor account.
        """
        return len(self.driver.find_elements_by_xpath('//*[@id="HardsellOverlay"]/div/div/div/div/div/div/div/div[1]/div[1]/div/div[2]/button')) > 0

    def _newerThanGivenYears(self):
        """
        A function that returns a boolean whether the oldest scraped review is less than given maximum age.
        Sometimes a featured review may occur, which disables to compute time_delta.
        Not to overcomplicate dropping these records during the scraping, we just look up to the first non-featured review
        through while and try&except loop.
        we 
        """
        if sum(datarow['Company'] == self.company_name for datarow in self.data) > 0:
            last_date = None
            t = 1
            while last_date == None:
                try:
                    last_date = datetime.datetime.strptime(
                            '-'.join(
                                [str(self.data[-t]['Year']), str(self.data[-t]['Month']), str(self.data[-t]['Day'])]
                                ), '%Y-%m-%d'
                        ).date()
                    time_delta = (self.current_date - last_date).days / 365
                except:
                    t += 1
            return time_delta < self.max_review_age
        else:
            return True
    
    def _parseMainText(self):
        """
        Parse review main text. This usually contains information about the relationship of the reviewer and company.
        """
        try:
            self.mainText = re.search('<p class="mainText mb-0">(.+?)</p>', self.reviewHTML).group(1)
        except:
            self.mainText = str()
    
    def _parseRecommendationBar(self):
        """
        A function that handles parsing the whole recommendation bar into a single elements
            - recommendation of a company - (with values of recommends, doesn't recommend, none)
            - outlook; values - (with values of positive, neutral, negative, none)
            - approves of ceo - (with values of approves, no opinon, disapproves, none)
        :param recommendationBar:
        """
        try:
            self.recommendationBar = {}
            recommendationBar = re.findall('<div class="col-sm-4">(.+?)</div>', self.reviewHTML)
            self.recommendationBarItems = [re.search('<span>(.+?)</span>', item).group(1) for item in recommendationBar]
            
            self.recommendationBar['Recommendation'] = self._parseRecommendationBar_Recommendation()
            self.recommendationBar['Outlook'] = self._parseRecommendationBar_Outlook()
            self.recommendationBar['OpinionOfCEO'] = self._parseRecommendationBar_CEO()
            
        except: # it is applied when no element of recommendation bar is present in a given review
            self.recommendationBar = {
                'Recommend': None,
                'Outlook': None,
                'CEO': None
            }
    
    def _parseRecommendationBar_CEO(self):
        """
        A helper function returning a reviewer's opinion of CEO.
        """
        try:
            itemCEO = [' '.join(item.split()[:-2]) for item in self.recommendationBarItems if 'ceo' in item.lower()]
            return itemCEO[0]
        except:
            return None
    
    def _parseRecommendationBar_Outlook(self):
        """
        A helper function returning a reviewer's outlook on a company.
        """
        try:
            itemOutlook = [item.split()[0] for item in self.recommendationBarItems if 'outlook' in item.lower()]
            return itemOutlook[0]
        except:
            return None

    def _parseRecommendationBar_Recommendation(self):
        """
        A helper function returning a statement whether a reviewer would recommend a given company.
        """
        try:
            itemRecommendation = [item for item in self.recommendationBarItems if 'recommend' in item.lower()]
            return itemRecommendation[0]
        except:
            return None
    
    def _parseReviewBody(self):
        """
        Parse review body containing 'Pros', 'Cons' and 'Advice to management element'   
        :param reviewHTML:
        """
        _reviewHTML = re.sub('\r|\n', '', self.reviewHTML)
        tabs = re.findall(  '<p class="strong mb-0 mt-xsm">(.+?)</p>', _reviewHTML)
        tabsText=re.findall(
            '<p class="mt-0 mb-xsm v2__EIReviewDetailsV2__bodyColor v2__EIReviewDetailsV2__lineHeightLarge v2__EIReviewDetailsV2__isExpanded ">(.+?)</p>',
            _reviewHTML
        )
        self.parsedReviewBody = {tab: tabText for tab, tabText in zip(tabs, tabsText)}

    def _parseReviewElements(self):
        """
        There are multiple objects in a review which need to be parsed.
        This function unites all the individual components together.
        Usage of this function is appropraite as it enables someone to avoid
        using one sub-fuction more than once (as this would be redundant).
        """
        self._parseRecommendationBar() # necessary to obtain attributes: 'Recommendation', 'Outlook', 'OpinionOfCEO'
        self._parseReviewBody() # necessary to obtain attributes: 'Pros', 'Cons' and 'Advice to Management'
        self._parseMainText() # this contains information on whether an employee is/was full-time/part-time and on a period of contract
        self._parseTimestamp() # get a timestamp

    def _parseTimestamp(self):
        """
        Parse review timestamp from review-HTML if available.
        """
        try:
            self.timestamp = re.search('<time class="date subtle small" datetime="(.+?)">', self.reviewHTML).group(1)
        except:
            self.timestamp = 'Featured Review'
    
    def _selectFirstCompany(self):
        """
        If more companies are found under a given keyword, the first returned result is chosen by this function.
        """
        firstCompany = self.driver.find_elements_by_class_name('single-company-result')[0]
        companyLink = re.search(
            f'<h2><a href="(.+?)">{self.company_name}(.+?)</h2>',
            firstCompany.get_attribute('outerHTML')).group(1)
        link = 'https://www.glassdoor.com' + companyLink
        print(link)
        self.getURL(link)
        time.sleep(1)

    def _sortReviewsMostRecent(self):
        """
        This function sorts the reviews so that most recent ones are liste first.
        As it is complicated to unroll list with sorting optins, url address is amended with an appendix
        """
        url = self.driver.current_url + '?sort.sortType=RD&sort.ascending=false'
        self.getURL(url)
    
    def _writeRowToDjangoDB(self, datarow):
        """
        :param datarow:
        """
        try:
            reviewRecord = self.ReviewWriter(
                CompanyID = 0,
                Company = datarow['Company'],
                ReviewTitle = datarow['ReviewTitle'],
                Year = datarow['Year'],
                Month = datarow['Month'],
                Day = datarow['Month'],
                Rating = datarow['Rating'],
                JobTitle = datarow['JobTitle'],
                EmployeeRelationship = datarow['EmployeeRelationship'],
                Location = datarow['Location'],
                Recommendation = datarow['Recommendation'],
                Outlook = datarow['Outlook'],
                OpinionOfCEO = datarow['OpinionOfCEO'],
                Contract = datarow['Contract'],
                ContractPeriod = datarow['ContractPeriod'],
                Pros = datarow['Pros'],
                Cons = datarow['Cons'],
                AdviceToManagement = datarow['AdviceToManagement'],
                Timestamp = datarow['Timestamp']
            )
            reviewRecord.save()
        except Exception as e:
            print(e)