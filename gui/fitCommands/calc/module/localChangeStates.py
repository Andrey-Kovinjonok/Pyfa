import wx
from logbook import Logger

import eos.db
from eos.saveddata.module import Module
from gui.fitCommands.helpers import restoreCheckedStates
from service.fit import Fit


pyfalog = Logger(__name__)


class CalcChangeLocalModuleStatesCommand(wx.Command):

    def __init__(self, fitID, mainPosition, positions, click):
        wx.Command.__init__(self, True, 'Change Module States')
        self.fitID = fitID
        self.mainPosition = mainPosition
        self.positions = positions
        self.click = click
        self.savedStates = {}
        self.savedStateCheckChanges = None

    def Do(self):
        pyfalog.debug('Doing change of local module states at position {}/{} to click {} on fit {}'.format(self.mainPosition, self.positions, self.click, self.fitID))
        sFit = Fit.getInstance()
        fit = sFit.getFit(self.fitID)
        mainMod = fit.modules[self.mainPosition]
        if mainMod.isEmpty:
            return False
        positions = [pos for pos in self.positions if not fit.modules[pos].isEmpty]
        self.savedStates = {pos: fit.modules[pos].state for pos in positions}

        changed = False
        mainProposedState = Module.getProposedState(mainMod, self.click)
        pyfalog.debug('Attempting to change modules to {}'.format(mainProposedState))
        if mainProposedState != mainMod.state:
            pyfalog.debug('Toggle {} state: {} for fit ID: {}'.format(mainMod, mainProposedState, self.fitID))
            mainMod.state = mainProposedState
            changed = True
            for position in [pos for pos in positions if pos != self.mainPosition]:
                mod = fit.modules[position]
                proposedState = Module.getProposedState(mod, self.click, mainProposedState)
                if proposedState != mod.state:
                    pyfalog.debug('Toggle {} state: {} for fit ID: {}'.format(mod, proposedState, self.fitID))
                mod.state = proposedState
        if not changed:
            return False
        # Need to flush because checkStates sometimes relies on module->fit
        # relationship via .owner attribute, which is handled by SQLAlchemy
        eos.db.flush()
        sFit.recalc(fit)
        self.savedStateCheckChanges = sFit.checkStates(fit, mainMod)
        eos.db.commit()
        return True

    def Undo(self):
        pyfalog.debug('Undoing change of local module states at position {}/{} to click {} on fit {}'.format(self.mainPosition, self.positions, self.click, self.fitID))
        fit = Fit.getInstance().getFit(self.fitID)
        for position, state in self.savedStates.items():
            mod = fit.modules[position]
            pyfalog.debug('Reverting {} to state {} for fit ID {}'.format(mod, state, self.fitID))
            mod.state = state
        restoreCheckedStates(fit, self.savedStateCheckChanges)
        eos.db.commit()
        return True
