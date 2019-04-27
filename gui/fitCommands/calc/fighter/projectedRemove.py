import wx
from logbook import Logger

import eos.db
from gui.fitCommands.helpers import FighterInfo
from service.fit import Fit


pyfalog = Logger(__name__)


class CalcRemoveProjectedFighterCommand(wx.Command):

    def __init__(self, fitID, position, commit=True):
        wx.Command.__init__(self, True, 'Add Projected Fighter')
        self.fitID = fitID
        self.position = position
        self.commit = commit
        self.savedFighterInfo = None

    def Do(self):
        pyfalog.debug('Doing removal of projected fighter at position {} from fit {}'.format(self.position, self.fitID))
        fit = Fit.getInstance().getFit(self.fitID)
        fighter = fit.projectedFighters[self.position]
        self.savedFighterInfo = FighterInfo.fromFighter(fighter)
        fit.projectedFighters.remove(fighter)
        if self.commit:
            eos.db.commit()
        return True

    def Undo(self):
        pyfalog.debug('Undoing removal of projected fighter at position {} from fit {}'.format(self.position, self.fitID))
        from .projectedAdd import CalcAddProjectedFighterCommand
        cmd = CalcAddProjectedFighterCommand(fitID=self.fitID, fighterInfo=self.savedFighterInfo, commit=self.commit)
        return cmd.Do()
