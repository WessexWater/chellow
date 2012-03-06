from django.db import models

class Asset(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', null=True)

    class Meta:
        db_table = 'asset'

    def parents(self):
        parent_list = []
        
        cand_parent = self.parent
        
        while True:
            if cand_parent is None:
                break
            else:
                parent_list.append(cand_parent)
                cand_parent = cand_parent.parent
                
        return parent_list
        
    def streams(self):
        return Stream.objects.filter(asset=self)
    
    
class Stream(models.Model):
    asset = models.ForeignKey('Asset')
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    properties = models.TextField()

    class Meta:
        db_table = 'stream'
        
        
class Advance(models.Model):
    stream = models.ForeignKey('Stream')
    start_date = models.DateTimeField()
    value = models.FloatField()

    class Meta:
        db_table = 'advance'
        unique_together = (('stream', 'start_date'),)
        

class Importer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    properties = models.TextField()
    
    class Meta:
        db_table = 'importer'