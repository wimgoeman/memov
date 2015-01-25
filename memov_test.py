#!/usr/bin/python

import unittest
from memov import Memov, get_config
import config
import os
import shutil

class MemovMock(Memov):
    def __init__(self):
        config.MOVIE_DIR = "/movies/"
        config.MUSIC_DIR = "/music/"
        config.TV_SHOW_DIR = "/shows/"
        config.EXTENSIONS = ["avi", "mp4", "iso", "mkv", "m4v", "sub", "srt"]
        config.MOVIE_INDICATORS = ["dvdrip", "dvd-rip", "xvid", "divx", "h264", "x264", "720p", "RARBG"]
        Memov.__init__(self)
        self.orig_file = ""
        self.new_file = ""  
        self.album = None   
        self.artist = None

    def createDir(self, tv_show_dir):
        pass
        
    def moveFile(self, orig_file, new_file):
        self.orig_file = orig_file
        self.new_file = new_file 

    def get_mp3_info(self, file):
        return self.artist, self.album

    def get_flac_info(self, file):
        return self.artist, self.album
        
class MemovFilesActivatedMock(Memov):
    def __init__(self):
        config.MOVIE_DIR = "test/Movies"
        config.TV_SHOW_DIR = "test/Shows"
        config.EXTENSIONS = ["avi", "mp4", "iso", "mkv", "m4v", "sub", "srt"]
        config.MOVIE_INDICATORS = ["dvdrip", "dvd-rip", "xvid", "divx", "h264", "x264", "720p", "RARBG"]
        config.XBMC_HOST = ''
        Memov.__init__(self)                   

class MemovTest(unittest.TestCase):
    def setUp(self):
        self.memov_mock = MemovMock()

    def testMovieAviXvid(self):
        self.memov_mock.move("/Downloads/", "Nymphomaniac 2013 Volume II UNRATED WEBRip XviD MP3-RARBG.avi") 
        self.assertEqual(self.memov_mock.new_file, "/movies/Nymphomaniac 2013 Volume II UNRATED WEBRip XviD MP3-RARBG.avi")   
        
    def testMovieDvdMinusRip(self):
        self.memov_mock.move("/Downloads/", "Marilyn Manson - Guns, God and Government World Tour - DVD-rip 480x272 PSP - NLizer.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/movies/Marilyn Manson - Guns, God and Government World Tour - DVD-rip 480x272 PSP - NLizer.mp4")       
        
    def testMovie720p(self):
        self.memov_mock.move("/Downloads/", "lion king 720p - zeberzee.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/movies/lion king 720p - zeberzee.mp4")     
        
    def testMoviePartlyDownloaded(self):
        self.memov_mock.move("/Downloads/", "Nymphomaniac 2013 Volume II UNRATED WEBRip XviD MP3-RARBG.avi.part") 
        self.assertEqual(self.memov_mock.new_file, "")            
                
    def testTvShowSmallCaseSerie(self):
        self.memov_mock.move("/Downloads/", "Family.Guy.s12e14.HDTV.x264-2HD.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/shows/Family Guy/Family Guy - Season 12/Family.Guy.S12E14.HDTV.x264-2HD.mp4")
        
    def testTvShowOnlyEpisodeInfo(self):
        self.memov_mock.move("/Downloads/", "Family Guy s8 e14.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/shows/Family Guy/Family Guy - Season 8/Family.Guy.S08E14.mp4")
        
    def testTvShowSpaceAfterEpisodeInfo(self):
        self.memov_mock.move("/Downloads/", "The.Simpsons.S25E14- HDTV.x264-LOL.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/shows/The Simpsons/The Simpsons - Season 25/The.Simpsons.S25E14.HDTV.x264-LOL.mp4")
        
    def testTvShowDoubleEpisode(self):
        self.memov_mock.move("/Downloads/", "Drop.Dead.Diva.S06E01-E02.HDTV.x264-2HD.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/shows/Drop Dead Diva/Drop Dead Diva - Season 6/Drop.Dead.Diva.S06E01-E02.HDTV.x264-2HD.mp4")        
        
    @unittest.skip("To be implemented")
    def testTvShowLittleEpisodeInfoSeason3(self):
        self.memov_mock.move("/Downloads/", "revenge.307.hdtv-lol.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/shows/Revenge/Revenge - Season 3/Revenge.S03E07.hdtv-lol.mp4")  
    
    @unittest.skip("To be implemented")    
    def testTvShowLittleEpisodeInfoSeason10(self):
        self.memov_mock.move("/Downloads/", "greys.anatomy.1018.hdtv-lol.mp4") 
        self.assertEqual(self.memov_mock.new_file, "/shows/Greys Anatomy/Greys Anatomy - Season 10/Greys.Anatomy.S10E18.hdtv-lol.mp4")           
    
    def testTvShowPartlyDownloaded(self):
        self.memov_mock.move("/Downloads/", "Revenge.S03E10.HDTV.x264-LOL.mp4.part") 
        self.assertEqual(self.memov_mock.new_file, "")                      

    def testTvShowS00Ep00(self):
        self.memov_mock.move("/Downloads/", "Breaking Bad s02ep7 720p brrip.sujaidr.mkv")
        self.assertEqual(self.memov_mock.new_file, "/shows/Breaking Bad/Breaking Bad - Season 2/Breaking.Bad.S02E07 720p brrip.sujaidr.mkv")

    def testMovieCrappyName(self):
        self.memov_mock.move("/Downloads/", "RARBG.com.avi")
        self.assertEqual(self.memov_mock.new_file, "/movies/RARBG.com.avi")
                
    def testMusicDashedFile(self):
        self.memov_mock.move("/Downloads/", "01 - An Awesome Song.mp3")
        self.assertEqual(self.memov_mock.new_file, "/music/Unknown artist/01 - An Awesome Song.mp3")

    def testMusicDottedFileWithArtist(self):
        self.memov_mock.artist = "Queen"
        self.memov_mock.move("/Downloads/", "Bohemian.Rhapsody.flac")
        self.assertEqual(self.memov_mock.new_file, "/music/Queen/Unknown album/Bohemian.Rhapsody.flac")
                
    def testMusicWithArtistAndAlbum(self):
        self.memov_mock.artist = "Queen"
        self.memov_mock.album = "Greatest Hits"
        self.memov_mock.move("/Downloads/", "Bohemian.Rhapsody.flac")
        self.assertEqual(self.memov_mock.new_file, "/music/Queen/Greatest Hits/Bohemian.Rhapsody.flac")
    
    def testMusicWithAlbumOnly(self):
        self.memov_mock.album = "Greatest Hits"
        self.memov_mock.move("/Downloads/", "Bohemian.Rhapsody.flac")
        self.assertEqual(self.memov_mock.new_file, "/music/Unknown artist/Bohemian.Rhapsody.flac")

    def testConfigList(self):
        config = ["a", "b", "c"]
        result = self.memov_mock._createConfigList(config)
        self.assertEqual(result, "a|b|c")

    def testMisingCriticalConfig(self):
        if hasattr(config, "DOWNLOAD_DIR"):
            del config.DOWNLOAD_DIR
        with self.assertRaises(SystemExit) as cm:
            get_config("DOWNLOAD_DIR", True)
        self.assertEqual(cm.exception.code, 1)

    def testMisingNonCriticalConfig(self):
        if hasattr(config, "DOWNLOAD_DIR"):
            del config.DOWNLOAD_DIR

        try:
            get_config("DOWNLOAD_DIR")
        except:
            self.fail("No exception should be thrown")
        
    def testFileAndDirectoryHandling(self):
        os.makedirs('test/Download')
        os.makedirs('test/Movies')
        open('test/Download/Nymphomaniac 2013 Volume II UNRATED WEBRip XviD MP3-RARBG.avi', 'a').close()    

        memov = MemovFilesActivatedMock()
        memov.run('test/Download')
        self.assertTrue(os.path.isfile('test/Movies/Nymphomaniac 2013 Volume II UNRATED WEBRip XviD MP3-RARBG.avi'))    
        
        shutil.rmtree('test/')
                                  
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(MemovTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
